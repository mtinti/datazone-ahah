"""The mapping, the schema and the edition checks, against the pinned files and against
hostile rows."""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest
import yaml

from ahah_ingest import checks, columns
from ahah_ingest.core import output
from ahah_ingest.core.checks import Report
from ahah_ingest.core.sources import load_registry
from ahah_ingest.reader import load_mapping, read_datazone_list, read_edition

REGISTRY = load_registry()
SCHEMA = output.load_schema(columns.SCHEMA)
MAPPING = load_mapping()
HAVE_FILES = all((REGISTRY.root / e["file"]).is_file() for e in REGISTRY.editions)
needs_files = pytest.mark.skipif(not HAVE_FILES, reason="pinned source files not present")


def test_generated_mapping_and_schema_match_the_files(tmp_path, monkeypatch):
    headers = {}
    for e in REGISTRY.editions:
        path = REGISTRY.root / e["file"]
        if not path.is_file():
            pytest.skip("pinned source files not present")
        headers[e["version"]] = open(path, encoding="utf-8").readline().rstrip("\r\n").split(",")
    monkeypatch.setattr(columns, "MAPPING", tmp_path / "m.yaml")
    monkeypatch.setattr(columns, "SCHEMA", tmp_path / "s.yaml")
    columns.write(headers)
    assert (tmp_path / "m.yaml").read_text() == columns.PACKAGE.joinpath("mapping.yaml").read_text()
    assert (tmp_path / "s.yaml").read_text() == columns.PACKAGE.joinpath("output_schema.yaml").read_text()


def test_every_file_column_maps_once_and_only_to_schema_columns():
    names = {f["name"] for f in SCHEMA["fields"]}
    for version, m in MAPPING.items():
        assert len(set(m.values())) == len(m), version
        assert set(m.values()) <= names, version
        expected = {f["name"] for f in SCHEMA["fields"] if version in f["editions"]} - {"ahah_version", "datazone_vintage"}
        assert set(m.values()) == expected, version


def test_the_twelve_heal_scot_columns_are_in_version_4():
    wanted = {"LSOA21CD": "datazone_code", "ah4dent": "dentist", "ah4gp": "GP", "ah4hosp": "hospital",
              "ah4phar": "pharmacy", "ah4h": "domain_h", "ah4g": "domain_g", "ah4e": "domain_e", "ah4r": "domain_r",
              "ah4ahah": "ahah", "ah4ahah_rnk": "ahah_rnk", "ah4ahah_pct": "ahah_pct"}
    assert {k: MAPPING["4"][k] for k in wanted} == wanted


def test_v1_and_v2_domains_go_to_the_exponential_columns():
    assert MAPPING["1"]["h"] == "domain_h_exp" and MAPPING["2"]["g_exp"] == "domain_g_exp"
    assert MAPPING["3"]["h"] == "domain_h" and MAPPING["4"]["ah4e"] == "domain_e"
    assert "domain_g_exp" not in MAPPING["1"].values()


def test_unknown_column_is_refused():
    with pytest.raises(ValueError):
        columns.mappings({"3": ["lsoa11", "ahah", "mystery"]})
    with pytest.raises(ValueError):
        columns.mappings({"4": ["LSOA21CD", "gp"]})


def _v4_rows():
    e = REGISTRY.edition("4")
    report = Report()
    frame = read_edition(REGISTRY.root / e["file"], e, MAPPING["4"], SCHEMA, report)
    return e, frame


@needs_files
def test_v4_rows_pass_and_a_tampered_row_fails():
    e, frame = _v4_rows()
    zones = read_datazone_list(REGISTRY.root / REGISTRY.datazone_lists[2011]["file"], REGISTRY.datazone_lists[2011])
    report = Report()
    checks.check_edition(frame, e, SCHEMA, zones, report)
    assert not report.blocking_failures
    # S01008132's air domain of -1.0000 is an ordinary value and passed above. A -1 drive time is not.
    assert frame.loc[frame["datazone_code"] == "S01008132", "domain_e"].iloc[0] == Decimal("-1.0000")
    bad = frame.copy()
    bad.loc[0, "GP"] = Decimal(-1)
    bad.loc[1, "ahah_pct"] = 0
    bad.loc[2, "GP_rnk"] = e["gb_rows"] + 1
    bad.loc[3, "ahah_rnk"] = bad.loc[4, "ahah_rnk"]
    bad.loc[5, "ur"] = 1
    bad.loc[6, "datazone_code"] = "S01999999"
    report = Report()
    checks.check_edition(bad, e, SCHEMA, zones, report)
    names = {c.name for c in report.blocking_failures}
    assert {"v4.GP.range", "v4.no_minus_one_code", "v4.ahah_pct.range", "v4.GP_rnk.range", "v4.ahah_rnk_unique",
            "v4.presence_matrix", "v4.every_zone_of_2011_present_once"} <= names


@needs_files
def test_v2_no_route_code_is_accepted_only_in_the_two_zones():
    e = REGISTRY.edition("2")
    frame = read_edition(REGISTRY.root / e["file"], e, MAPPING["2"], SCHEMA, Report())
    zones = read_datazone_list(REGISTRY.root / REGISTRY.datazone_lists[2011]["file"], REGISTRY.datazone_lists[2011])
    report = Report()
    checks.check_edition(frame, e, SCHEMA, zones, report)
    assert not report.blocking_failures
    bad = frame.copy()
    i = bad.index[bad["datazone_code"] == "S01006506"][0]
    bad.loc[i, "GP_dec"] = -1
    report = Report()
    checks.check_edition(bad, e, SCHEMA, zones, report)
    assert "v2.no_route_code_zones" in {c.name for c in report.blocking_failures}
    # ur must be 0 or 1, and never NULL in version 2.
    bad = frame.copy()
    bad.loc[0, "ur"] = 2
    bad.loc[1, "ur"] = None
    report = Report()
    checks.check_edition(bad, e, SCHEMA, zones, report)
    assert {"v2.ur.range", "v2.presence_matrix"} <= {c.name for c in report.blocking_failures}


@needs_files
def test_reader_refuses_a_changed_header_or_row_count(tmp_path):
    e = REGISTRY.edition("1")
    text = open(REGISTRY.root / e["file"], encoding="utf-8").read().splitlines()
    (tmp_path / "short.csv").write_text("\n".join(text[:-1]) + "\n")
    report = Report()
    with pytest.raises(Exception):
        read_edition(tmp_path / "short.csv", e, MAPPING["1"], SCHEMA, report)
    assert "v1.gb_rows" in {c.name for c in report.blocking_failures}
    (tmp_path / "extra.csv").write_text("\n".join([text[0] + ",extra"] + [l + ",1" for l in text[1:]]) + "\n")
    report = Report()
    with pytest.raises(Exception):
        read_edition(tmp_path / "extra.csv", e, MAPPING["1"], SCHEMA, report)
    assert "v1.header_is_mapped" in {c.name for c in report.blocking_failures}


def test_registry_pins_both_vintages():
    assert set(REGISTRY.datazone_lists) == {2011, 2022}
    assert REGISTRY.datazone_lists[2011]["zones"] == 6976 and REGISTRY.datazone_lists[2022]["zones"] == 7392


@needs_files
def test_v2_code_is_forbidden_in_every_non_routed_decile_and_indicator():
    e = REGISTRY.edition("2")
    frame = read_edition(REGISTRY.root / e["file"], e, MAPPING["2"], SCHEMA, Report())
    zones = read_datazone_list(REGISTRY.root / REGISTRY.datazone_lists[2011]["file"], REGISTRY.datazone_lists[2011])
    i = frame.index[frame["datazone_code"] == "S01006506"][0]
    j = frame.index[frame["datazone_code"] == "S01010206"][0]   # one of the two no-route zones
    for col in ("greenspace_dec", "greenspace_active_dec", "NO2_dec", "PM10_dec", "SO2_dec", "NO2", "greenspace"):
        for row in (i, j):
            bad = frame.copy()
            bad.loc[row, col] = -1 if col.endswith("_dec") else Decimal(-1)
            report = Report()
            checks.check_edition(bad, e, SCHEMA, zones, report)
            names = {c.name for c in report.blocking_failures}
            assert "v2.no_route_code_outside_routed" in names, (col, row)
            assert f"v2.{col}.range" in names, (col, row)
    # The allowed case: a routed decile of a no-route zone already holds -1 and passes.
    assert frame.loc[j, "GP_dec"] == -1
    report = Report()
    checks.check_edition(frame, e, SCHEMA, zones, report)
    assert not report.blocking_failures
