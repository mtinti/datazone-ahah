"""Write the frozen schema to Parquet with table-level metadata, and read it back to verify."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from .checks import Report
from .sources import sha256
from .text_output import DECIMAL_PRECISION, DECIMAL_SCALE, INTEGER_KINDS, _is_null

ARROW = {"string": pa.string(), "int8": pa.int8(), "int16": pa.int16(), "int32": pa.int32(),
         "decimal": pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE)}

RANK_CONVENTION = ("Every rank, percentile and decile reads 1 as the healthiest area, the opposite of SIMD. "
                   "Ranks are over Great Britain, not Scotland. Editions are not comparable with each other: "
                   "use one edition per study and never compare editions over time.")


def load_schema(path: Path) -> dict:
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw["key"], list) or not raw["key"]:
        raise ValueError(f"{path}: key must be a non-empty list")
    for f in raw["fields"]:
        if f["type"] not in ARROW:
            raise ValueError(f"{path}: {f['name']} has unsupported type {f['type']!r}")
    return {"version": raw["version"], "table": raw["table"], "key": list(raw["key"]),
            "fields": raw["fields"], "sha256": sha256(path)}


def table_metadata(registry, schema: dict, decisions_sha256: str) -> dict:
    return {"rank_convention": RANK_CONVENTION, "schema_version": schema["version"], "key": schema["key"],
            "decisions_sha256": decisions_sha256, "registry_sha256": registry.sha256,
            "sources": [{"version": e["version"], "file": e["file"], "sha256": e["sha256"]} for e in registry.editions]}


def arrow_schema(schema: dict, metadata: dict) -> pa.Schema:
    fields = [pa.field(f["name"], ARROW[f["type"]], nullable=bool(f["nullable"])) for f in schema["fields"]]
    return pa.schema(fields, metadata={k: (v if isinstance(v, str) else json.dumps(v)) for k, v in metadata.items()})


def _column(series: pd.Series, field: dict) -> pa.Array:
    kind = field["type"]
    if kind == "string":
        return pa.array([None if _is_null(v) else str(v) for v in series], type=pa.string())
    if kind == "decimal":
        # Each value is a Decimal; Arrow stores it exactly at the declared scale.
        values = []
        for v in series:
            if _is_null(v):
                values.append(None)
            elif isinstance(v, Decimal):
                values.append(v)
            else:
                raise TypeError(f"{field['name']}: not a Decimal: {v!r}")
        return pa.array(values, type=ARROW[kind])
    if kind in INTEGER_KINDS:
        if field["nullable"]:
            return pa.array([None if _is_null(v) else int(v) for v in series], type=ARROW[kind])
        return pa.array([int(v) for v in series], type=ARROW[kind])
    raise ValueError(f"unsupported type {kind!r}")


def write_table(table: pd.DataFrame, schema: dict, path: Path, metadata: dict) -> str:
    arrow = arrow_schema(schema, metadata)
    arrays = [_column(table[f["name"]], f) for f in schema["fields"]]
    pa_table = pa.Table.from_arrays(arrays, schema=arrow)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    pq.write_table(pa_table, part, compression="zstd", write_statistics=True)
    os.replace(part, path)
    return sha256(path)


def read_table(path: Path) -> pd.DataFrame:
    """The saved Parquet as pandas, decimals as Decimal objects, integers nullable."""
    table = pq.read_table(path)
    frame = {}
    for field in table.schema:
        column = table.column(field.name)
        if pa.types.is_decimal(field.type):
            frame[field.name] = pd.Series(column.to_pylist(), dtype=object)
        elif pa.types.is_integer(field.type):
            frame[field.name] = pd.Series(column.to_pylist(), dtype="Int64")
        else:
            frame[field.name] = pd.Series(column.to_pylist(), dtype="string")
    return pd.DataFrame(frame)


def readback(path: Path, schema: dict, accepted: pd.DataFrame, metadata: dict, report: Report,
             label: str = "readback.parquet") -> dict:
    """Reopen the saved file and compare its structure, metadata and every cell with the
    accepted table."""
    file = pq.ParquetFile(path)
    saved_schema = file.schema_arrow
    report.equal(f"{label}.column_names", saved_schema.names, [f["name"] for f in schema["fields"]])
    report.equal(f"{label}.column_types", [str(t) for t in saved_schema.types], [str(ARROW[f["type"]]) for f in schema["fields"]])
    report.equal(f"{label}.nullability", [f.nullable for f in saved_schema], [bool(f["nullable"]) for f in schema["fields"]])
    report.require()
    meta = saved_schema.metadata or {}
    expected_meta = arrow_schema(schema, metadata).metadata
    for key, expected in expected_meta.items():
        actual = meta.get(key)
        report.equal(f"{label}.metadata.{key.decode()}",
                     actual.decode("utf-8", errors="replace") if actual is not None else None, expected.decode())
    saved = read_table(path)
    report.equal(f"{label}.rows", len(saved), len(accepted))
    report.equal(f"{label}.primary_key_unique", int(saved.duplicated(schema["key"]).sum()), 0)
    report.require()
    differences = {}
    for f in schema["fields"]:
        name = f["name"]
        a, b = saved[name].tolist(), accepted[name].tolist()
        n = sum(1 for x, y in zip(a, b) if not ((_is_null(x) and _is_null(y)) or (not _is_null(x) and not _is_null(y) and x == y)))
        if n:
            differences[name] = n
    report.equal(f"{label}.cells", differences, {}, detail=f"{len(schema['fields'])} columns compared")
    return {"table": schema["table"], "schema_version": schema["version"], "schema_sha256": schema["sha256"],
            "key": schema["key"], "rows": len(saved), "columns": len(saved.columns), "sha256": sha256(path)}
