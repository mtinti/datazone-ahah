"""The column provenance site: every column traced, every reference real, no check cited that the
build does not emit, no pass claimed without a clean, known build (docs/AHAH_Provenance_Site_Plan.md).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from ahah_ingest.lineage import lineage, range_check
from ahah_ingest.provenance_site import describe_check, evidence, write
from ahah_ingest.pipeline import build_identity

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "ahah_ingest"
SCHEMA = yaml.safe_load((PACKAGE / "output_schema.yaml").read_text())
FIELDS = {f["name"]: f for f in SCHEMA["fields"]}
MAPPING = yaml.safe_load((PACKAGE / "mapping.yaml").read_text())["editions"]
DOCUMENTS = yaml.safe_load((PACKAGE / "documents.yaml").read_text())["documents"]
DESCRIPTIONS = yaml.safe_load((PACKAGE / "column_descriptions.yaml").read_text())["columns"]
DECISIONS = {d["id"] for d in yaml.safe_load((PACKAGE / "decisions.yaml").read_text())["decisions"]}
MANIFEST = ROOT / "results" / "manifest.json"


@pytest.fixture(scope="module")
def L():
    return lineage()


@pytest.fixture(scope="module")
def emitted():
    return {c["name"] for c in json.loads(MANIFEST.read_text())["checks"]}


# --- coverage --------------------------------------------------------------------------------------

def test_every_column_has_a_lineage_record_in_schema_order(L):
    assert list(L) == list(FIELDS) and len(L) == 90


def test_every_column_has_a_description_covering_every_edition_it_carries():
    assert set(DESCRIPTIONS) == set(FIELDS)
    for name, f in FIELDS.items():
        covered = {e for d in DESCRIPTIONS[name] for e in d["editions"]}
        assert covered == set(f["editions"]), name
        for d in DESCRIPTIONS[name]:
            assert d["kind"] in ("quotation", "paraphrase", "correction", "ours") and d["text"].strip(), name


def test_every_document_reference_resolves_by_hash_and_ours_needs_no_file():
    for did, d in DOCUMENTS.items():
        assert d["kind"] in ("pinned_document", "repository_document") and re.fullmatch(r"[0-9a-f]{64}", d["sha256"]), did
        if d["kind"] == "repository_document":
            path = ROOT / d["path"]
            assert path.is_file(), did
            from ahah_ingest.core.sources import sha256
            assert sha256(path) == d["sha256"], did
        else:
            pinned = (ROOT / "data" / "sources" / d["path"])
            if pinned.is_file():
                from ahah_ingest.core.sources import sha256
                assert sha256(pinned) == d["sha256"], did
            record = (ROOT / "data" / "sources" / d["path"].split("/")[0] / "SOURCES.md").read_text()
            assert d["sha256"] in record, did                     # the committed source record pins it
    for name, defs in DESCRIPTIONS.items():
        for d in defs:
            ref = d["reference"]
            if d["kind"] in ("quotation", "paraphrase", "correction"):
                assert ref["document"] in DOCUMENTS and ref.get("location"), (name, ref)
            else:
                assert "document" not in ref and ref.get("kind") == "ours", (name, ref)
                if ref.get("decision"):
                    assert ref["decision"] in DECISIONS, (name, ref)


# --- inputs follow the mapping and the presence matrix ---------------------------------------------

def test_inputs_are_exactly_the_mapped_file_columns_of_the_editions_that_publish_the_column(L):
    for name, r in L.items():
        for i in r["inputs"]:
            assert i["edition"] in FIELDS[name]["editions"], (name, i)
            if i["kind"] == "pinned_file":
                assert MAPPING[i["edition"]][i["field"]] == name, (name, i)
        assert sorted(i["edition"] for i in r["inputs"]) == sorted(FIELDS[name]["editions"]), name
        assert set(r["absent"]) == {"1", "2", "3", "4", "5.1"} - set(FIELDS[name]["editions"]), name


def test_the_hand_stated_cases(L):
    def inputs(name):
        return [(i["edition"], i["field"]) for i in L[name]["inputs"]]
    assert inputs("off_licence") == [("1", "off"), ("2", "off")]
    assert [e for e, _ in inputs("domain_h_exp")] == ["1", "2"] and [e for e, _ in inputs("domain_h")] == ["3", "4", "5.1"]
    assert inputs("ur") == [("2", "ur")]
    assert inputs("bluespace") == [("2", "blue"), ("3", "blue"), ("4", "ah4blue"), ("5.1", "bluespace")]
    assert inputs("greenspace_active") == [("2", "gact"), ("5.1", "greenspace_active")]
    assert [e for e, _ in inputs("bluespace_rnk")] == ["3", "4", "5.1"] and [e for e, _ in inputs("bluespace_dec")] == ["2"]
    assert [e for e, _ in inputs("greenspace_active_rnk")] == ["5.1"] and [e for e, _ in inputs("greenspace_active_dec")] == ["2"]
    assert inputs("datazone_code") == [("1", "lsoa11"), ("2", "lsoa11"), ("3", "lsoa11"), ("4", "LSOA21CD"), ("5.1", "lsoa21cd")]
    assert [i["kind"] for i in L["ahah_version"]["inputs"]] == ["registry"] * 5


def test_edition_scoped_descriptions():
    def defs(name, edition, kind=None):
        return [d for d in DESCRIPTIONS[name] if edition in d["editions"] and (kind is None or d["kind"] == kind)]
    assert defs("GP", "1")[0]["unit"] == "kilometres" and defs("GP", "3", "quotation")[0]["unit"] == "minutes"
    assert "NDVI" in defs("greenspace", "3", "quotation")[0]["text"] and "NDVI" not in defs("greenspace", "1")[0]["text"]
    assert "A&E" in defs("hospital", "5.1", "quotation")[0]["text"] and not defs("hospital", "4", "quotation")
    assert "unconfirmed" in defs("GP", "2")[0]["text"].lower() and defs("GP", "2")[0]["kind"] == "ours"
    code = defs("datazone_code", "5.1")
    assert any(d["kind"] == "quotation" and "(2011)" in d["text"] for d in code)
    assert any(d["kind"] == "correction" and "2022" in d["text"] and d["reference"]["document"] == "v5_methodology" for d in code)


def test_edition_1_definitions_follow_the_paper():
    """Daras et al. 2019: A&E hospitals only (page 3); green space per postcode within a 900 m buffer
    (page 4); the third domain is physical environment, green space plus NO2, PM10 and SO2 (pages 3 to 5)."""
    def v1(name):
        return [d for d in DESCRIPTIONS[name] if "1" in d["editions"]][0]
    assert "accident and emergency" in v1("hospital")["text"] and v1("hospital")["reference"]["document"] == "daras2019"
    three_four = [d for d in DESCRIPTIONS["hospital"] if "3" in d["editions"]][0]
    assert "unconfirmed" in three_four["text"] and "5.1 only" not in three_four["text"]
    assert "each postcode" in v1("greenspace")["text"] and "buffer of the area" not in v1("greenspace")["text"]
    for name in ("domain_e_exp", "domain_e_dec"):
        assert "physical environment" in v1(name)["text"] and "green space" in v1(name)["text"], name
        assert v1(name)["reference"]["document"] == "daras2019" and v1(name)["kind"] == "paraphrase"
    later = [d for d in DESCRIPTIONS["domain_e"] if "3" in d["editions"] and d["kind"] == "ours"][0]
    assert "air quality" in later["text"]
    for name in ("domain_h_pct", "ahah_pct"):
        assert "(or 0)" not in [d for d in DESCRIPTIONS[name] if "3" in d["editions"]][0]["text"]


# --- checks: exact names the build emits, ranges only where it range-checks ---------------------------

def test_every_cited_check_is_emitted_by_the_build_by_exact_name(L, emitted):
    cited = {c for r in L.values() for c, _ in r["checks"]}
    assert sorted(cited - emitted) == []
    assert all(describe_check(c) for c in cited)


def test_range_checks_only_where_the_build_emits_them(L, emitted):
    for name, r in L.items():
        for v in FIELDS[name]["editions"]:
            expected = f"v{v}.{name}.range"
            cited = expected in {c for c, _ in r["checks"]}
            assert cited == (expected in emitted), (name, v)
            assert (range_check(FIELDS[name], v) == expected) == cited
    for name in ("ahah_version", "datazone_vintage", "datazone_code", "ahah", "domain_h", "domain_g", "domain_e", "domain_r"):
        assert not any(c.endswith(".range") for c, _ in L[name]["checks"]), name
    assert ("v4.GP.range", "column") in L["GP"]["checks"] and ("v4.GP_rnk.range", "column") in L["GP_rnk"]["checks"]
    assert ("v1.domain_h_exp.range", "column") in L["domain_h_exp"]["checks"] and ("v2.domain_g_exp.range", "column") in L["domain_g_exp"]["checks"]


def test_every_column_cites_the_edition_wide_checks_and_its_own(L):
    for name, r in L.items():
        names = {c for c, _ in r["checks"]}
        for v in FIELDS[name]["editions"]:
            assert {f"v{v}.presence_matrix", f"v{v}.header_is_mapped", f"v{v}.no_empty_cells"} <= names, (name, v)
        assert "table.key_unique" in names
    assert "v5.1.ahah_rnk_unique" in {c for c, _ in L["ahah_rnk"]["checks"]}
    assert {"v2.no_route_code_zones", "v2.no_route_code_outside_routed"} <= {c for c, _ in L["GP_dec"]["checks"]}
    assert not any("no_route" in c for c, _ in L["NO2"]["checks"])


def test_absent_editions_cite_the_presence_check_that_makes_the_column_null(L):
    for name, r in L.items():
        for v in r["absent"]:
            assert (f"v{v}.presence_matrix", "edition") in r["checks"], (name, v)
            assert not any(c.startswith(f"v{v}.") and c != f"v{v}.presence_matrix" for c, _ in r["checks"]), (name, v)
    assert [c for c, _ in L["off_licence"]["checks"] if c.endswith("presence_matrix")] == [f"v{v}.presence_matrix" for v in ("1", "2", "3", "4", "5.1")]


def test_readback_checks_are_cited_one_by_one(L):
    names = {c for c, _ in L["GP"]["checks"]}
    assert {"readback.parquet.column_names", "readback.parquet.column_types", "readback.parquet.nullability", "readback.parquet.rows",
            "readback.parquet.primary_key_unique", "readback.parquet.cells", "readback.csv.header", "readback.csv.rows", "readback.csv.cells"} <= names


def test_check_descriptions_state_the_real_scope():
    """The reader compares header names as sets and checks empty cells only in Scottish rows: a
    reversed header and an empty English cell both pass, so the descriptions must not claim more."""
    import tempfile
    from ahah_ingest.core.checks import Report
    from ahah_ingest.reader import read_edition
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "v.csv"
        path.write_text("gp,lsoa11\n1.5,S01000001\n,E01000001\n")
        report = Report()
        read_edition(path, {"version": "1", "gb_rows": 2, "vintage": 2011, "code_column": "lsoa11"},
                     {"lsoa11": "datazone_code", "gp": "GP"}, SCHEMA, report)
        results = {c["name"]: c["passed"] for c in report.to_records()}
    assert results["v1.header_is_mapped"] is True and results["v1.no_empty_cells"] is True
    assert "order is not checked" in describe_check("v1.header_is_mapped")
    assert "Scottish row" in describe_check("v1.no_empty_cells") and "England and Wales are not checked" in describe_check("v1.no_empty_cells")
    assert "every cell" in describe_check("readback.parquet.cells") and "metadata" not in describe_check("readback.parquet.cells")
    assert describe_check("readback.parquet.column_types") != describe_check("readback.parquet.cells")


def test_every_decision_exists(L):
    assert {d for r in L.values() for d in r["decisions"]} <= DECISIONS and all(r["decisions"] for r in L.values())


# --- build identity and evidence --------------------------------------------------------------------

def _manifest(**over):
    m = json.loads(MANIFEST.read_text())
    m.update(over)
    return m


def test_a_manifest_without_identity_shows_definitions_only():
    m = _manifest()
    m.pop("build", None)
    ev = evidence(m)
    assert ev["usable"] is False and "no build identity" in ev["reason"] and "label" not in ev


def test_a_dirty_or_unknown_build_shows_no_pass_label():
    base = _manifest()
    for identity in ({"commit": "unknown", "dirty": None, "modified": []},
                     {"commit": "a" * 40, "dirty": True, "modified": ["ahah_ingest/reader.py"]},
                     {"commit": "a" * 40, "dirty": None, "modified": []}):
        ev = evidence(base | {"build": identity})
        assert ev["usable"] is False and "label" not in ev, identity
    clean = evidence(base | {"build": {"commit": "a" * 40, "dirty": False, "modified": [], "package_version": "0.1.0", "schema_version": "s"}})
    assert clean["usable"] is True and "aaaaaaa" in clean["label"]


def test_a_changed_configuration_hash_is_named():
    ev = evidence(_manifest(registry_sha256="0" * 64))
    assert "registry" in ev["changed"]
    assert evidence(_manifest())["changed"] == []


def test_a_changed_configuration_is_shown_on_the_column_page_with_the_results(tmp_path, monkeypatch):
    m = _manifest(registry_sha256="0" * 64, mapping_sha256="1" * 64,
                  build={"commit": "c" * 40, "dirty": False, "modified": [], "package_version": "0.1.0", "schema_version": SCHEMA["version"]})
    monkeypatch.setattr("ahah_ingest.provenance_site.MANIFEST", tmp_path / "manifest.json")
    (tmp_path / "manifest.json").write_text(json.dumps(m))
    out = tmp_path / "site"
    write(out)
    page = (out / "columns" / "GP.md").read_text()
    assert "build `ccccccc`" in page and "| pass |" in page
    assert "Changed since that build:** `registry`, `mapping`" in page


def test_the_site_never_borrows_its_own_commit_for_evidence(tmp_path, monkeypatch):
    m = _manifest()
    m.pop("build", None)
    monkeypatch.setattr("ahah_ingest.provenance_site.MANIFEST", tmp_path / "manifest.json")
    (tmp_path / "manifest.json").write_text(json.dumps(m))
    out = tmp_path / "site"
    counts = write(out)
    assert counts["evidence"] is False
    page = (out / "columns" / "GP.md").read_text()
    assert "No build result is shown" in page and "| Result |" not in page
    assert "Check evidence:** none shown" in (out / "index.md").read_text()


def test_a_clean_build_shows_results_and_a_failure_is_shown_as_such(tmp_path, monkeypatch):
    m = _manifest(build={"commit": "b" * 40, "dirty": False, "modified": [], "package_version": "0.1.0", "schema_version": SCHEMA["version"]})
    for c in m["checks"]:
        if c["name"] in ("v4.GP.range", "v3.presence_matrix"):
            c["passed"] = False
    monkeypatch.setattr("ahah_ingest.provenance_site.MANIFEST", tmp_path / "manifest.json")
    (tmp_path / "manifest.json").write_text(json.dumps(m))
    out = tmp_path / "site"
    assert write(out)["evidence"] is True
    page = (out / "columns" / "GP.md").read_text()
    assert "build `bbbbbbb`" in page and "`v4.GP.range`: FAIL" in page
    assert "| pass |" in (out / "columns" / "dentist.md").read_text()
    # A presence failure in an edition where the column must be NULL is visible on that column's page.
    absent = (out / "columns" / "off_licence.md").read_text()
    assert "`v3.presence_matrix`: FAIL" in absent


def test_build_identity_records_the_commit_and_cleanliness(tmp_path):
    identity = build_identity()
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", identity["commit"])
    assert identity["dirty"] in (True, False, None) and identity["package_version"] and identity["schema_version"] == SCHEMA["version"]
    import shutil
    shutil.copy(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    outside = build_identity(tmp_path)
    assert outside["commit"] == "unknown" and outside["dirty"] is None and outside["modified"] == []


# --- the generated site ----------------------------------------------------------------------------

def test_the_site_has_a_page_per_column_and_every_link_resolves(tmp_path):
    counts = write(tmp_path)
    assert counts["columns"] == 90 and counts["editions"] == 5 and counts["decisions"] == len(DECISIONS)
    column_pages = {p.stem for p in (tmp_path / "columns").glob("*.md") if p.stem != "index" and not p.stem.startswith("group-")}
    assert column_pages == set(FIELDS)
    for page in tmp_path.rglob("*.md"):
        for target in re.findall(r"\]\(([^)#]+\.md)\)", page.read_text()):
            assert (page.parent / target).resolve().is_file(), (page.name, target)


def test_every_check_name_on_a_page_is_an_emitted_one(tmp_path, emitted):
    write(tmp_path)
    for page in (tmp_path / "columns").glob("*.md"):
        text = page.read_text()
        for names in re.findall(r"<!-- (.*?) -->", text):
            assert set(names.split()) <= emitted, page.name
        for name in re.findall(r"^\| `((?:source|table|readback|decimal)[^`]*)`", text, re.M):
            assert name in emitted, (page.name, name)


def test_quotations_are_marked_and_the_v5_dictionary_is_not_applied_to_edition_1(tmp_path):
    write(tmp_path)
    page = (tmp_path / "columns" / "GP.md").read_text()
    assert "“Drive-time to nearest GP Practice (minutes)”" in page and "quoted from" in page
    v1 = (tmp_path / "editions" / "1.md").read_text()
    assert "kilometres" in v1 and "Drive-time" not in v1


def test_the_edition_page_keeps_the_quotation_with_its_correction(tmp_path):
    write(tmp_path)
    v51 = (tmp_path / "editions" / "5.1.md").read_text()
    row = next(l for l in v51.splitlines() if l.startswith("| `lsoa21cd` |"))
    assert "“Lower Super Output Area Code (2011) / Data Zones (Scotland)” (quoted," in row
    assert "**Correction:**" in row and "2022 data zones" in row
    hospital = next(l for l in (tmp_path / "editions" / "4.md").read_text().splitlines() if l.startswith("| `ah4hosp` |"))
    assert "unconfirmed" in hospital
    v1 = (tmp_path / "editions" / "1.md").read_text()
    assert "physical environment" in v1 and "accident and emergency" in v1


def test_the_conventions_page_exists_and_is_linked_from_percentile_pages(tmp_path):
    write(tmp_path)
    page = (tmp_path / "conventions.md").read_text()
    assert "## Why indicator percentiles run 0 to 100" in page and "healthiest" in page
    assert "[Ranks and percentiles](../conventions.md)" in (tmp_path / "columns" / "GP_pct.md").read_text()
    assert "docs/PERCENTILES.md" not in (tmp_path / "columns" / "GP_pct.md").read_text().split("## Where it comes from")[0]


def test_regeneration_removes_pages_no_longer_written(tmp_path):
    write(tmp_path)
    stale = tmp_path / "columns" / "a_dropped_column.md"
    stale.write_text("# gone")
    write(tmp_path)
    assert not stale.exists() and (tmp_path / "columns" / "ahah.md").is_file()
