"""The checks on the assembled table: presence per edition, ranges, codes, reference lists."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from .columns import DOMAINS, INDICATORS, OLD_INDICATORS, ROUTED
from .core.checks import Report
from .core.text_output import _is_null

# Version 2 publishes -1 ("no route", unconfirmed) in eleven routed indicators and their
# deciles for exactly these two zones, both Glasgow City, both with a 2017 population of 0.
V2_NO_ROUTE_ZONES = {"S01010206", "S01010226"}
ROUTED_WITH_BLUE = ROUTED + ["bluespace"]


def _nonnull(series: pd.Series) -> pd.Series:
    return series[[not _is_null(v) for v in series]]


def _range(report: Report, label: str, series: pd.Series, low, high, name: str) -> None:
    values = _nonnull(series)
    bad = int(sum(1 for v in values if not (low <= v <= high)))
    report.equal(f"{label}.{name}.range", bad, 0, detail=f"{len(values)} values in [{low}, {high}]" if not bad else f"{bad} outside [{low}, {high}]")


def check_edition(frame: pd.DataFrame, edition: dict, schema: dict, zones: list, report: Report) -> None:
    version = edition["version"]
    label = f"v{version}"
    part = frame[frame["ahah_version"] == version]
    report.equal(f"{label}.scottish_rows", len(part), len(zones))
    codes = set(part["datazone_code"])
    missing, extra = sorted(set(zones) - codes), sorted(codes - set(zones))
    report.equal(f"{label}.every_zone_of_{edition['vintage']}_present_once", {"missing": missing[:5], "extra": extra[:5]},
                 {"missing": [], "extra": []}, detail=f"{len(zones)} zones of the pinned list, each once" if not (missing or extra) else f"{len(missing)} missing, {len(extra)} extra")
    report.equal(f"{label}.vintage", set(part["datazone_vintage"].tolist()), {int(edition["vintage"])})

    # Presence: NULL exactly where the edition lacks the column.
    wrong = {}
    for f in schema["fields"]:
        nulls = int(sum(1 for v in part[f["name"]] if _is_null(v)))
        expected = 0 if version in f["editions"] else len(part)
        if nulls != expected:
            wrong[f["name"]] = nulls
    report.equal(f"{label}.presence_matrix", wrong, {}, detail=f"{len(schema['fields'])} columns, NULL only where the edition has no column")

    n = edition["gb_rows"]
    for f in schema["fields"]:
        name = f["name"]
        if version not in f["editions"]:
            continue
        s = part[name]
        if name.endswith("_rnk"):
            _range(report, label, s, 1, n, name)
        elif name.endswith("_pct"):
            low = 0 if f["group"] == "indicator_pct" else 1
            _range(report, label, s, low, 100, name)
        elif name.endswith("_dec"):
            if version == "2" and f["group"] == "indicator_dec" and name[:-4] in ROUTED_WITH_BLUE:
                ok = s[[v != -1 for v in s]]
                _range(report, label, ok, 1, 10, name)
            else:
                _range(report, label, s, 1, 10, name)
        elif name == "ur":
            _range(report, label, s, 0, 1, name)
        elif name in ROUTED_WITH_BLUE or name in ("NO2", "PM10", "SO2", "greenspace", "greenspace_active"):
            if version == "2" and name in ROUTED_WITH_BLUE:
                s = s[[v != Decimal(-1) for v in s]]
            _range(report, label, s, Decimal(0), Decimal("1e18"), name)
        elif f["group"] == "domain_exp":
            _range(report, label, s, Decimal(0), Decimal(100), name)
    # The overall rank identifies the zone.
    if version in {f["name"]: f for f in schema["fields"]}["ahah_rnk"]["editions"]:
        report.equal(f"{label}.ahah_rnk_unique", int(part["ahah_rnk"].duplicated().sum()), 0)

    # The version 2 code: in the named zones, in routed indicators and their deciles, nowhere else.
    if version == "2":
        where = set()
        for name in ROUTED_WITH_BLUE:
            for col in (name, f"{name}_dec"):
                for code, v in zip(part["datazone_code"], part[col]):
                    if not _is_null(v) and v == -1:
                        where.add(code)
        report.equal(f"{label}.no_route_code_zones", where, V2_NO_ROUTE_ZONES)
        # Outside the routed columns the code is forbidden everywhere, the two zones included.
        bad = 0
        for name in INDICATORS + OLD_INDICATORS:
            if name not in ROUTED_WITH_BLUE:
                bad += sum(1 for v in part[f"{name}_dec"] if not _is_null(v) and v == -1)
                bad += sum(1 for v in part[name] if not _is_null(v) and v == -1)
        report.equal(f"{label}.no_route_code_outside_routed", bad, 0)
    else:
        bad = 0
        for name in ROUTED_WITH_BLUE + [f"{i}_dec" for i in INDICATORS + OLD_INDICATORS]:
            if name in part:
                bad += sum(1 for v in part[name] if not _is_null(v) and v == -1)
        report.equal(f"{label}.no_minus_one_code", bad, 0)


def check_table(frame: pd.DataFrame, schema: dict, report: Report) -> None:
    report.equal("table.key_unique", int(frame.duplicated(schema["key"]).sum()), 0)
    nulls = {f["name"]: int(sum(1 for v in frame[f["name"]] if _is_null(v))) for f in schema["fields"] if not f["nullable"]}
    report.equal("table.required_nonnull", {k: v for k, v in nulls.items() if v}, {})
    report.equal("table.columns", list(frame.columns), [f["name"] for f in schema["fields"]])
