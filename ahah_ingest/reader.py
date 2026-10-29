"""Read one edition's file as text, keep the Scottish rows, map the columns, parse the values.

Nothing is read through a float. Scores are parsed with Decimal, ranks and bands with int.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml

from .columns import MAPPING
from .core.checks import Report
from .core.text_output import INTEGER_KINDS, parse_decimal

SCOTTISH_PREFIX = "S01"


def load_mapping(path: Path = MAPPING) -> dict:
    raw = yaml.safe_load(Path(path).read_text())
    if raw.get("version") != 1:
        raise ValueError("Unsupported mapping version")
    return raw["editions"]


def read_edition(path: Path, edition: dict, mapping: dict, schema: dict, report: Report) -> pd.DataFrame:
    """The edition's Scottish rows as a frame with the table's columns, every value typed.

    Checks, each blocking: the header is exactly the mapped columns; the Great Britain row
    count equals the publisher's summary; the Scottish codes are distinct; no mapped cell is
    empty.
    """
    version = edition["version"]
    label = f"v{version}"
    kinds = {f["name"]: f["type"] for f in schema["fields"]}
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    report.equal(f"{label}.header_is_mapped", sorted(header), sorted(mapping),
                 detail=f"{len(header)} columns" if sorted(header) == sorted(mapping) else
                 f"unmapped {sorted(set(header) - set(mapping))}, missing {sorted(set(mapping) - set(header))}")
    report.equal(f"{label}.header_unique", len(set(header)), len(header))
    report.equal(f"{label}.gb_rows", len(rows), edition["gb_rows"], detail=f"{len(rows)} rows before the Scottish filter")
    report.require()
    code_at = header.index(edition["code_column"])
    widths = {len(r) for r in rows}
    report.equal(f"{label}.row_width", widths, {len(header)})
    report.require()
    scottish = [r for r in rows if r[code_at].startswith(SCOTTISH_PREFIX)]
    codes = [r[code_at] for r in scottish]
    report.equal(f"{label}.scottish_codes_distinct", len(set(codes)), len(codes))
    report.equal(f"{label}.scottish_code_shape", sum(1 for c in codes if len(c) != 9 or not c[3:].isdigit()), 0,
                 detail="every code is S01 and six digits")
    empty = {}
    for i, name in enumerate(header):
        n = sum(1 for r in scottish if r[i].strip() == "")
        if n:
            empty[name] = n
    report.equal(f"{label}.no_empty_cells", empty, {})
    report.require()

    out = {"ahah_version": pd.Series([version] * len(scottish), dtype="string"),
           "datazone_vintage": pd.Series([int(edition["vintage"])] * len(scottish), dtype="Int64")}
    for i, name in enumerate(header):
        target = mapping[name]
        kind = kinds[target]
        raw = [r[i] for r in scottish]
        if kind == "string":
            out[target] = pd.Series(raw, dtype="string")
        elif kind == "decimal":
            out[target] = pd.Series([parse_decimal(v) for v in raw], dtype=object)
        elif kind in INTEGER_KINDS:
            values = []
            for v in raw:
                d = Decimal(v.strip())
                if d != d.to_integral_value():
                    raise ValueError(f"{label} {target}: {v!r} is not an integer")
                values.append(int(d))
            out[target] = pd.Series(values, dtype="Int64")
        else:
            raise ValueError(kind)
    frame = pd.DataFrame(out)
    for f in schema["fields"]:
        if f["name"] not in frame:
            frame[f["name"]] = pd.Series([None] * len(frame), dtype=("object" if f["type"] == "decimal" else "Int64" if f["type"] in INTEGER_KINDS else "string"))
    return frame[[f["name"] for f in schema["fields"]]]


def read_datazone_list(path: Path, spec: dict) -> list:
    """The codes of one vintage's reference list."""
    with open(path, encoding=spec["encoding"], newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [r[spec["code_column"]] for r in rows]
