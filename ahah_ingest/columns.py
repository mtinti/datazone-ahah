"""The table's columns and how each edition's file columns map onto them.

The table uses the version 5.1 names. Earlier editions use short names (`gp`, `hosp`, ...),
version 4 the same short names with an `ah4` prefix. This module writes the explicit per-edition
mapping and the output schema as files, so that both are reviewable and the build reads only
the files; `python -m ahah_ingest.columns` regenerates them and the tests check they match.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PACKAGE = Path(__file__).resolve().parent
MAPPING = PACKAGE / "mapping.yaml"
SCHEMA = PACKAGE / "output_schema.yaml"
SCHEMA_VERSION = "ahah_datazone_v1"
TABLE = "ahah_datazone"
KEY = ["ahah_version", "datazone_code"]

# The 15 indicators of version 5.1, in its file order, then the one only older editions have.
INDICATORS = ["GP", "bluespace", "dentist", "fast_food", "gambling", "greenspace_active", "hospital",
              "leisure", "pharmacy", "pub_bar", "tobacco", "NO2", "PM10", "SO2", "greenspace"]
OLD_INDICATORS = ["off_licence"]
DOMAINS = ["domain_h", "domain_g", "domain_e", "domain_r"]

# Short name (versions 1 to 4) to table name.
SHORT = {"gp": "GP", "blue": "bluespace", "dent": "dentist", "ffood": "fast_food", "gamb": "gambling",
         "gact": "greenspace_active", "hosp": "hospital", "leis": "leisure", "phar": "pharmacy",
         "pubs": "pub_bar", "tob": "tobacco", "no2": "NO2", "pm10": "PM10", "so2": "SO2",
         "gpas": "greenspace", "off": "off_licence",
         "h": "domain_h", "g": "domain_g", "e": "domain_e", "r": "domain_r", "ahah": "ahah"}
# Routed indicators: a drive distance or time, never negative except the version 2 "no route" code.
ROUTED = ["GP", "dentist", "pharmacy", "hospital", "leisure", "gambling", "fast_food", "pub_bar",
          "tobacco", "off_licence"]

# Edition presence of each column group, "y" or "-", as the SQL plan's matrix states it.
PRESENCE = {
    "indicator": {"1": True, "2": True, "3": True, "4": True, "5.1": True},
    "bluespace": {"1": False, "2": True, "3": True, "4": True, "5.1": True},
    "greenspace_active": {"1": False, "2": True, "3": False, "4": False, "5.1": True},
    "off_licence": {"1": True, "2": True, "3": False, "4": False, "5.1": False},
    "ur": {"1": False, "2": True, "3": False, "4": False, "5.1": False},
    "indicator_rnk": {"1": False, "2": False, "3": True, "4": True, "5.1": True},
    "indicator_pct": {"1": False, "2": False, "3": True, "4": True, "5.1": True},
    "indicator_dec": {"1": True, "2": True, "3": False, "4": False, "5.1": False},
    "domain": {"1": False, "2": False, "3": True, "4": True, "5.1": True},
    "domain_exp": {"1": True, "2": True, "3": False, "4": False, "5.1": False},
    "domain_g_exp": {"1": False, "2": True, "3": False, "4": False, "5.1": False},
    "domain_rnk": {"1": False, "2": True, "3": True, "4": True, "5.1": True},
    "domain_pct": {"1": False, "2": False, "3": True, "4": True, "5.1": True},
    "domain_dec": {"1": True, "2": True, "3": False, "4": False, "5.1": False},
    "domain_g_any": {"1": False, "2": True, "3": True, "4": True, "5.1": True},
    "ahah": {"1": True, "2": True, "3": True, "4": True, "5.1": True},
    "ahah_rnk": {"1": False, "2": True, "3": True, "4": True, "5.1": True},
    "ahah_pct": {"1": False, "2": False, "3": True, "4": True, "5.1": True},
    "ahah_dec": {"1": True, "2": True, "3": False, "4": False, "5.1": False},
}
VERSIONS = ["1", "2", "3", "4", "5.1"]


def _field(name, kind, group, description, nullable=True):
    return {"name": name, "type": kind, "nullable": nullable, "group": group,
            "editions": [v for v in VERSIONS if present(name, group, v)], "description": description}


def present(name: str, group: str, version: str) -> bool:
    """Whether an edition publishes a column: the group's row of the matrix, narrowed by the
    exceptions for the three indicators not every edition has and for the green domain."""
    if group == "key":
        return True
    base = PRESENCE[group][version]
    stem = name if group in ("indicator", "ur", "ahah", "domain", "domain_exp") else name.rsplit("_", 1)[0]
    if group == "domain_exp":
        stem = name[:-4]
    if stem in ("bluespace", "greenspace_active", "off_licence"):
        base = base and PRESENCE[stem][version]
    if stem == "domain_g":
        base = base and PRESENCE["domain_g_any"][version]
        if group == "domain_exp":
            base = PRESENCE["domain_g_exp"][version]
    return base


def schema_fields() -> list:
    f = []
    f.append(_field("ahah_version", "string", "key", "AHAH edition: 1, 2, 3, 4 or 5.1. Editions are not comparable with each other.", nullable=False))
    f.append(_field("datazone_vintage", "int16", "key", "Scottish data zone vintage the edition is on: 2011 for editions 1 to 4, 2022 for 5.1.", nullable=False))
    f.append(_field("datazone_code", "string", "key", "Scottish data zone code (S01...). The code of the vintage in datazone_vintage.", nullable=False))
    for name in INDICATORS + OLD_INDICATORS:
        f.append(_field(name, "decimal", "indicator", f"Indicator value as published. Units differ by edition: see the data dictionary."))
    f.append(_field("ur", "int8", "ur", "Version 2 only: a 0/1 flag the v2 build code does not use, probably urban = 1. Not documented."))
    for name in INDICATORS:
        f.append(_field(f"{name}_rnk", "int32", "indicator_rnk", "Rank over Great Britain, 1 is the healthiest."))
    for name in INDICATORS:
        f.append(_field(f"{name}_pct", "int8", "indicator_pct", "Percentile over Great Britain, 0 to 100 (101 values): int(rank / max rank * 100). See docs/PERCENTILES.md."))
    for name in INDICATORS + OLD_INDICATORS:
        f.append(_field(f"{name}_dec", "int16", "indicator_dec", "Decile over Great Britain, 1 to 10, 1 is the healthiest. Version 2 publishes -1 in two zones with no route."))
    for name in DOMAINS:
        f.append(_field(name, "decimal", "domain", "Domain score, probit scale, as published (editions 3, 4 and 5.1)."))
    for name in DOMAINS:
        f.append(_field(f"{name}_exp", "decimal", "domain_exp", "Domain score of editions 1 and 2: the exponentially transformed domain rank, 0 to 100, 100 is the worst rank. Not the probit scale of the later editions."))
    for name in DOMAINS:
        f.append(_field(f"{name}_rnk", "int32", "domain_rnk", "Domain rank over Great Britain, 1 is the healthiest."))
    for name in DOMAINS:
        f.append(_field(f"{name}_pct", "int8", "domain_pct", "Domain percentile over Great Britain, 1 to 100: qcut of the rank into 100 bins. See docs/PERCENTILES.md."))
    for name in DOMAINS:
        f.append(_field(f"{name}_dec", "int16", "domain_dec", "Domain decile over Great Britain, 1 to 10, 1 is the healthiest."))
    f.append(_field("ahah", "decimal", "ahah", "Overall index score as published: the mean of the exponentially transformed domain ranks (three domains in edition 1, four from edition 2). In editions 3 onward the published domain scores are the probit-scale intermediates, on a different scale; the index does not average them, it averages their ranks after the exponential transformation (v4 create_index.py lines 99 to 104)."))
    f.append(_field("ahah_rnk", "int32", "ahah_rnk", "Overall rank over Great Britain, 1 is the healthiest. Unique within an edition: it identifies the data zone."))
    f.append(_field("ahah_pct", "int8", "ahah_pct", "Overall percentile over Great Britain, 1 to 100."))
    f.append(_field("ahah_dec", "int16", "ahah_dec", "Overall decile over Great Britain, 1 to 10, 1 is the healthiest."))
    return f


def _table_name(file_column: str, version: str) -> str:
    """The table column a file column maps to, or a ValueError."""
    c = file_column
    if version == "4":
        if not c.startswith("ah4"):
            raise ValueError(f"v4 column without ah4 prefix: {c}")
        c = c[3:]
    stem, suffix = (c.rsplit("_", 1) + [""])[:2] if "_" in c else (c, "")
    if suffix not in ("rnk", "pct", "dec", "exp"):
        stem, suffix = c, ""
    if version == "1" and stem in ("h", "e", "r") and suffix == "":
        return f"{SHORT[stem]}_exp"
    if version == "5.1":
        return c
    if version == "2" and c == "ur":
        return "ur"
    if stem not in SHORT:
        raise ValueError(f"unknown v{version} column {file_column}")
    return SHORT[stem] + (f"_{suffix}" if suffix else "")


def mappings(headers: dict) -> dict:
    """`headers`: version to the file's header list. Returns version to {file column: table column}."""
    out = {}
    for version, columns in headers.items():
        code = columns[0]
        m = {code: "datazone_code"}
        for c in columns[1:]:
            m[c] = _table_name(c, version)
        if len(set(m.values())) != len(m):
            raise ValueError(f"v{version}: two file columns map to one table column")
        out[version] = m
    return out


def write(headers: dict) -> None:
    fields = schema_fields()
    names = {f["name"] for f in fields}
    maps = mappings(headers)
    for version, m in maps.items():
        unknown = sorted(set(m.values()) - names)
        if unknown:
            raise ValueError(f"v{version} maps to columns not in the schema: {unknown}")
        expected = {f["name"] for f in fields if version in f["editions"]} - {"ahah_version", "datazone_vintage"}
        if set(m.values()) != expected:
            raise ValueError(f"v{version}: presence matrix and mapping disagree: "
                             f"only in matrix {sorted(expected - set(m.values()))}, only in file {sorted(set(m.values()) - expected)}")
    MAPPING.write_text("# File column to table column, per edition. Generated by python -m ahah_ingest.columns\n"
                       "# from the pinned files' headers; every file column appears exactly once.\n"
                       + yaml.safe_dump({"version": 1, "editions": maps}, sort_keys=False))
    SCHEMA.write_text("# Frozen output schema of ahah_datazone. Order, type and nullability are the contract.\n"
                      "# Generated by python -m ahah_ingest.columns; do not edit by hand.\n"
                      + yaml.safe_dump({"version": SCHEMA_VERSION, "table": TABLE, "key": KEY,
                                        "columns": len(fields), "fields": fields}, sort_keys=False))


def main(argv=None) -> int:
    from .core.sources import load_registry
    registry = load_registry()
    headers = {}
    for ed in registry.editions:
        with open(registry.root / ed["file"], encoding="utf-8", newline="") as fh:
            headers[ed["version"]] = fh.readline().rstrip("\r\n").split(",")
    write(headers)
    print(f"wrote {MAPPING}\nwrote {SCHEMA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
