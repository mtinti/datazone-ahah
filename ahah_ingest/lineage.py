"""Column lineage: for every column of ahah_datazone, where its value comes from and how.

One record per column, built from mapping.yaml, the presence matrix, the registry, the SQL
declarations and the build's own check rules, never typed by hand
(docs/AHAH_Provenance_Site_Plan.md, section 2). A record holds:

- inputs: one per edition that publishes the column: the pinned file, its SHA256, the file
  column read, and the join key by which the value reaches the row;
- absent: the editions in which the column is NULL;
- transformation: its kind, the rule in words, and the code that applies it;
- checks: the exact names of the build checks that guard it, each with its scope (the column,
  the whole edition, a source file, the table, or the readback), as the build emits them; the
  presence check of every edition is cited, including the editions where the column must be
  NULL; whether a build passed them is in that build's manifest.json["checks"];
- decisions: ids from decisions.yaml;
- export: the CSV column and the SQL Server type.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml

from .checks import ROUTED_WITH_BLUE
from .columns import MAPPING, SCHEMA, VERSIONS
from .core.sources import load_registry
from .sql_check import SQL_DECLARED, SQL_TYPE

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
RAW_INDICATORS = set(ROUTED_WITH_BLUE) | {"NO2", "PM10", "SO2", "greenspace", "greenspace_active"}


@functools.lru_cache(maxsize=None)
def _context() -> dict:
    registry = load_registry(PACKAGE / "sources.yaml")
    mapping = yaml.safe_load((PACKAGE / "mapping.yaml").read_text())["editions"]
    schema = yaml.safe_load((PACKAGE / "output_schema.yaml").read_text())
    reverse = {v: {table: file for file, table in m.items()} for v, m in mapping.items()}
    return {"registry": registry, "mapping": mapping, "reverse": reverse, "schema": schema}


def sql_type(kind: str) -> str:
    return SQL_DECLARED.get(kind, SQL_TYPE[kind])


def range_check(field: dict, version: str) -> str | None:
    """The name of the range check the build emits for this column in this edition, or None:
    the same branches as checks.check_edition, so that no check is cited that never runs."""
    name, group = field["name"], field["group"]
    if version not in field["editions"]:
        return None
    ranged = (name.endswith(("_rnk", "_pct", "_dec")) or name == "ur" or name in RAW_INDICATORS
              or group == "domain_exp")
    return f"v{version}.{name}.range" if ranged else None


def _edition_checks(field: dict, version: str, vintage: str) -> list:
    """Every check of the edition that guards this column, by exact name and scope."""
    name = field["name"]
    checks = [(f"v{version}.presence_matrix", "edition"),
              (f"v{version}.header_is_mapped", "edition"), (f"v{version}.header_unique", "edition"),
              (f"v{version}.row_width", "edition"), (f"v{version}.no_empty_cells", "edition"),
              (f"v{version}.gb_rows", "edition"), (f"v{version}.scottish_rows", "edition"),
              (f"v{version}.scottish_code_shape", "edition"), (f"v{version}.scottish_codes_distinct", "edition"),
              (f"v{version}.every_zone_of_{vintage}_present_once", "edition")]
    if name == "datazone_vintage":
        checks.append((f"v{version}.vintage", "column"))
    r = range_check(field, version)
    if r:
        checks.append((r, "column"))
    if name == "ahah_rnk" and version in field["editions"]:
        checks.append((f"v{version}.ahah_rnk_unique", "column"))
    stem = name[:-4] if name.endswith("_dec") else name
    if version == "2" and stem in ROUTED_WITH_BLUE and (name == stem or name.endswith("_dec")):
        checks += [("v2.no_route_code_zones", "edition"), ("v2.no_route_code_outside_routed", "edition")]
    elif version != "2" and (name in ROUTED_WITH_BLUE or name.endswith("_dec") and field["group"] == "indicator_dec"):
        checks.append((f"v{version}.no_minus_one_code", "edition"))
    return checks


def _transformation(field: dict) -> dict:
    name, kind = field["name"], field["type"]
    if name == "ahah_version":
        return {"kind": "derived", "rule": "The edition's version label from the registry, written on every row read from that edition's file.",
                "code": "ahah_ingest.reader.read_edition"}
    if name == "datazone_vintage":
        return {"kind": "derived", "rule": "The edition's data zone vintage from the registry (2011 or 2022), written on every row.",
                "code": "ahah_ingest.reader.read_edition"}
    if name == "datazone_code":
        return {"kind": "key", "rule": "The edition's code column, copied as text; only rows whose code starts with S01 are kept, and the "
                "set of codes must equal the pinned data zone list of the vintage, each once.", "code": "ahah_ingest.reader.read_edition"}
    if kind == "decimal":
        return {"kind": "decimal", "rule": "The file text parsed with Python Decimal, never a float, so the value is exactly the published "
                "one (scientific notation in version 3 included); rendered with 20 fractional digits in the CSV. NULL where the edition "
                "has no such column.", "code": "ahah_ingest.reader.read_edition; ahah_ingest.core.text_output.render_decimal"}
    return {"kind": "int", "rule": "The file text parsed as an integer, as published. NULL where the edition has no such column.",
            "code": "ahah_ingest.reader.read_edition"}


def _decisions(field: dict) -> list:
    name, group = field["name"], field["group"]
    ids = ["one-table-all-editions", "v5-1-names"]
    if field["type"] == "decimal":
        ids.append("decimal-not-float")
    if name.endswith(("_rnk", "_dec")) or name == "ahah_rnk":
        ids.append("ranks-gb-only")
    if name.endswith("_pct"):
        ids += ["ranks-gb-only", "percentile-scales"]
    if group in ("domain", "domain_exp") or name == "ahah":
        ids.append("v1-v2-exponential-domains")
    stem = name[:-4] if name.endswith("_dec") else name
    if stem in ROUTED_WITH_BLUE and "2" in field["editions"]:
        ids.append("v2-no-route-code")
    if name == "ur":
        ids.append("ur-tinyint")
    if name in ("datazone_code", "datazone_vintage"):
        ids.append("datazone-lists")
    return list(dict.fromkeys(ids))


@functools.lru_cache(maxsize=None)
def lineage() -> dict:
    ctx = _context()
    registry = ctx["registry"]
    out = {}
    for f in ctx["schema"]["fields"]:
        name = f["name"]
        inputs, absent = [], []
        for ed in registry.editions:
            v = ed["version"]
            if v not in f["editions"]:
                absent.append(v)
                continue
            file_column = ctx["reverse"][v].get(name)
            if name in ("ahah_version", "datazone_vintage"):
                inputs.append({"kind": "registry", "edition": v, "path": "ahah_ingest/sources.yaml",
                               "field": "version" if name == "ahah_version" else "vintage", "join": None})
            else:
                assert file_column, (name, v)
                inputs.append({"kind": "pinned_file", "edition": v, "path": ed["file"], "sha256": ed["sha256"],
                               "field": file_column, "join": None if name == "datazone_code" else "the row's datazone_code"})
        checks = []
        for ed in registry.editions:
            if ed["version"] in f["editions"]:
                checks += _edition_checks(f, ed["version"], str(ed["vintage"]))
            else:
                # The column must be NULL in this edition: the presence check establishes that too.
                checks.append((f"v{ed['version']}.presence_matrix", "edition"))
        checks += [(f"source.{ed['file']}", "source") for ed in registry.editions if ed["version"] in f["editions"]]
        if name == "datazone_code":
            checks += [(f"source.{spec['file']}", "source") for spec in registry.datazone_lists.values()]
        checks += [("table.columns", "table"), ("table.key_unique", "table"), ("table.required_nonnull", "table"),
                   ("readback.parquet.column_names", "readback"), ("readback.parquet.column_types", "readback"),
                   ("readback.parquet.nullability", "readback"), ("readback.parquet.rows", "readback"),
                   ("readback.parquet.primary_key_unique", "readback"), ("readback.parquet.cells", "readback"),
                   ("readback.csv.header", "readback"), ("readback.csv.rows", "readback"), ("readback.csv.cells", "readback")]
        if f["type"] == "decimal":
            checks.append(("decimal_round_trip", "table"))
        out[name] = {"column": name, "group": f["group"], "type": f["type"], "nullable": f["nullable"],
                     "editions": list(f["editions"]), "absent": absent, "inputs": inputs,
                     "transformation": _transformation(f), "checks": checks, "decisions": _decisions(f),
                     "export": {"csv_column": name, "sql_type": sql_type(f["type"]), "in_digest": True}}
    return out
