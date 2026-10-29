"""The CSV rendering of the table, and the row digest a database load is checked against.

Copied from postcode-simd's simd_ingest/core/text_output.py and reduced to the types AHAH uses:
string, int8, int16, int32 and decimal. The digest framing is unchanged (definition version 1):
a null is a marker, fields are joined with a separator, each row is hashed, the signed
eight-byte prefixes are summed. A decimal is rendered in fixed notation with the contract's
number of fractional digits, never through a float.
"""

from __future__ import annotations

import gzip
import hashlib
from decimal import Decimal, localcontext
from pathlib import Path

import pandas as pd
import yaml

from .checks import Report
from .sources import sha256

INTEGER_KINDS = ("int8", "int16", "int32")
KINDS = ("string", "decimal") + INTEGER_KINDS
# decimal(38,20) on SQL Server: 18 integer digits at most.
DECIMAL_PRECISION, DECIMAL_SCALE = 38, 20


class ReservedCharacter(ValueError):
    """Source text contains a character the digest framing needs. Never stripped."""


class DecimalDoesNotFit(ValueError):
    """A value has more fractional digits than the column's scale, or too many digits in all."""


def load_contract(path: Path) -> dict:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    if raw.get("version") != 1:
        raise ValueError(f"Unsupported export contract version {raw.get('version')!r}")
    if raw["digest"]["version"] != 1 or raw["digest"]["hash"] != "sha256":
        raise ValueError("Unsupported digest definition")
    if raw["values"]["decimal_places"] != DECIMAL_SCALE:
        raise ValueError("The decimal rendering must match the SQL scale")
    raw["sha256"] = sha256(path)
    return raw


def exported_columns(schema: dict, contract: dict, table: str) -> list:
    spec = contract["tables"][table]
    excluded = set(spec["exclude"])
    names = [f["name"] for f in schema["fields"]]
    missing = excluded - set(names)
    if missing:
        raise ValueError(f"{table}: excluded columns are not in the schema: {sorted(missing)}")
    return [name for name in names if name not in excluded]


def render_decimal(value: Decimal, places: int = DECIMAL_SCALE) -> str:
    """Fixed notation with exactly `places` fractional digits. Refuses to round: a value with
    more digits than the scale does not fit the column and must stop the build, not be trimmed.
    Zero is never written with a sign, as SQL Server never writes one."""
    if not isinstance(value, Decimal):
        raise TypeError(f"not a Decimal: {value!r}")
    if not value.is_finite():
        raise DecimalDoesNotFit(f"{value} is not finite")
    if value == 0:
        value = Decimal(0)
    # The default context holds 28 digits; a decimal(38,20) needs 38. Quantising in a wider
    # context never rounds, so the equality test below is exact.
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION + places
        quantised = value.quantize(Decimal(1).scaleb(-places))
    if quantised != value:
        raise DecimalDoesNotFit(f"{value} has more than {places} fractional digits")
    text = f"{quantised:f}"
    digits = text.replace("-", "").replace(".", "")
    if len(digits.lstrip("0") or "0") > DECIMAL_PRECISION:
        raise DecimalDoesNotFit(f"{value} has more than {DECIMAL_PRECISION} digits")
    return text


def parse_decimal(text: str) -> Decimal:
    """The file's text as an exact Decimal, scientific notation included, never via float."""
    value = Decimal(text.strip())
    if not value.is_finite():
        raise DecimalDoesNotFit(f"{text!r} is not a finite number")
    return value


def _is_null(v) -> bool:
    return v is None or v is pd.NA or (isinstance(v, float) and v != v)


def render(table: pd.DataFrame, schema: dict, columns: list, contract: dict) -> pd.DataFrame:
    """Every exported value as text, with nulls marked."""
    kinds = {f["name"]: f["type"] for f in schema["fields"]}
    marker, reserved = contract["digest"]["null_marker"], contract["digest"]["reserved"]
    places = contract["values"]["decimal_places"]
    out = {}
    for name in columns:
        column, kind = table[name], kinds[name]
        if kind == "string":
            values = column.astype("string")
            found = [c for c in reserved if values.str.contains(c, regex=False, na=False).any()]
            if found:
                raise ReservedCharacter(f"{name}: source text contains {found!r}, which the digest framing reserves")
            values = values.fillna(marker)
        elif kind == "decimal":
            values = column.map(lambda v: marker if _is_null(v) else render_decimal(v, places))
        elif kind in INTEGER_KINDS:
            # A null is marked like any other null; it is never written as a number, and an
            # empty cell can never be read as zero.
            values = column.map(lambda v: marker if _is_null(v) else str(int(v)))
        else:
            raise ValueError(f"{name}: unsupported type {kind!r}")
        out[name] = values.astype("string")
    return pd.DataFrame(out, index=table.index)[columns]


def write_csv(rendered: pd.DataFrame, contract: dict, path: Path) -> dict:
    """The rendered table as CSV, nulls written as an empty cell."""
    dialect = contract["dialect"]
    path = Path(path)
    frame = rendered.replace(contract["digest"]["null_marker"], contract["values"]["empty"])
    text = frame.to_csv(index=False, sep=dialect["delimiter"], lineterminator=dialect["line_ending"])
    body = text.encode(dialect["encoding"])
    with open(path, "wb") as fh, gzip.GzipFile(filename="", fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(body)
    return {"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "uncompressed_bytes": len(body), "uncompressed_sha256": hashlib.sha256(body).hexdigest(),
            "rows": len(rendered), "columns": len(rendered.columns), "compression": dialect["compression"]}


def row_digest(rendered: pd.DataFrame, contract: dict) -> dict:
    """One SHA-256 per row over the marked, separated fields; the signed eight-byte prefixes
    summed exactly, so the total does not depend on row order."""
    spec = contract["digest"]
    separator, size, signed = spec["separator"], spec["prefix_bytes"], spec["signed"]
    joined = rendered.iloc[:, 0]
    for name in rendered.columns[1:]:
        joined = joined + separator + rendered[name]
    total = 0
    for line in joined.to_numpy():
        total += int.from_bytes(hashlib.sha256(line.encode("utf-8")).digest()[:size], "big", signed=signed)
    return {"version": spec["version"], "rows": len(rendered), "total": str(total),
            "note": "compact probabilistic check for accidental load corruption, not a proof of identity"}


def readback_csv(path: Path, rendered: pd.DataFrame, contract: dict, report: Report, label: str) -> None:
    """Reopen the saved file as text and compare every cell with the rendered table."""
    expected = rendered.replace(contract["digest"]["null_marker"], contract["values"]["empty"])
    with gzip.open(path, "rt", encoding=contract["dialect"]["encoding"], newline="") as fh:
        saved = pd.read_csv(fh, dtype=str, keep_default_na=False, sep=contract["dialect"]["delimiter"])
    report.equal(f"{label}.header", list(saved.columns), list(expected.columns))
    report.equal(f"{label}.rows", len(saved), len(expected))
    report.require()
    differences = {}
    for name in expected.columns:
        differs = int((saved[name].to_numpy() != expected[name].to_numpy()).sum())
        if differs:
            differences[name] = differs
    report.equal(f"{label}.cells", differences, {}, detail=f"{len(expected.columns)} columns compared")
