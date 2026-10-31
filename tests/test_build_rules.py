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


def test_write_csv_reports_non_ascii_bytes(tmp_path):
    """The build's csv.ascii check reads this count: zero for the real table, counted otherwise."""
    import pandas as pd
    from ahah_ingest.core import text_output as tx
    contract = tx.load_contract(Path(__file__).resolve().parent.parent / "ahah_ingest" / "export_contract.yaml")
    clean = pd.DataFrame({"a": ["S01000001", "1.5"], "b": ["x", contract["digest"]["null_marker"]]})
    assert tx.write_csv(clean, contract, tmp_path / "c.csv.gz")["non_ascii_bytes"] == 0
    dirty = pd.DataFrame({"a": ["S01000001 ", "µ"], "b": ["x", "y"]})
    assert tx.write_csv(dirty, contract, tmp_path / "d.csv.gz")["non_ascii_bytes"] == 4   # C2 A0 and C2 B5


def _generations(tmp_path):
    from ahah_ingest.pipeline import OUTPUTS
    results, staging = tmp_path / "results", tmp_path / "results" / ".staging_1"
    staging.mkdir(parents=True)
    for name in OUTPUTS:
        (results / name).write_text(f"old {name}")
        (staging / name).write_text(f"new {name}")
    return results, staging


def _files(results):
    from ahah_ingest.pipeline import LOCK
    return {p.name: p.read_text() for p in results.iterdir() if p.is_file() and p.name != LOCK}


def test_promotion_interrupted_before_the_journal_leaves_the_old_generation(tmp_path, monkeypatch):
    import os
    from ahah_ingest.pipeline import OUTPUTS, promote, recover, verify_results
    results, staging = _generations(tmp_path)
    real = os.replace

    def failing(src, dst):
        if str(dst).endswith("manifest.json.new"):
            raise OSError("disk full")
        real(src, dst)
    monkeypatch.setattr(os, "replace", failing)
    with pytest.raises(OSError):
        promote(staging, results, OUTPUTS)
    assert _files(results) == {n: f"old {n}" for n in OUTPUTS}            # untouched, no .new, no journal
    assert not list(results.glob("*.new")) and not (results / ".promote.json").exists()
    assert recover(results) == "removed 1 leftover(s) of an unfinished build"   # the fixture's staging folder
    assert recover(results) == "nothing to recover"


def test_promotion_interrupted_after_the_journal_is_finished_forward_and_refused_meanwhile(tmp_path, monkeypatch):
    """The state a SIGKILL leaves between two renames: a mixture of old and new files plus the
    journal. Nothing was deleted; every consumer refuses it; recovery completes it."""
    import json, os
    from ahah_ingest.pipeline import JOURNAL, OUTPUTS, ResultsIncomplete, promote, recover, verify_results
    results, staging = _generations(tmp_path)
    real, swapped = os.replace, []

    def crashing(src, dst):
        if str(src).endswith(".new"):
            if len(swapped) == 1:
                raise KeyboardInterrupt                                   # the process dies after the first swap
            swapped.append(dst)
        real(src, dst)
    monkeypatch.setattr(os, "replace", crashing)
    with pytest.raises(ResultsIncomplete):
        promote(staging, results, OUTPUTS)
    monkeypatch.setattr(os, "replace", real)
    on_disk = _files(results)
    assert on_disk[OUTPUTS[0]] == f"new {OUTPUTS[0]}" and on_disk[OUTPUTS[1]] == f"old {OUTPUTS[1]}"   # the mixture
    assert (results / JOURNAL).exists() and (results / f"{OUTPUTS[1]}.new").read_text() == f"new {OUTPUTS[1]}"
    with pytest.raises(ResultsIncomplete):
        verify_results(results, files=False)
    assert recover(results) == "finished an interrupted promotion"
    assert _files(results) == {n: f"new {n}" for n in OUTPUTS}
    assert not (results / JOURNAL).exists() and not list(results.glob("*.new"))


def test_a_build_recovers_before_it_starts_and_a_pending_journal_blocks_promotion(tmp_path, monkeypatch):
    import json
    from ahah_ingest import pipeline
    from ahah_ingest.pipeline import JOURNAL, OUTPUTS, ResultsIncomplete, promote
    results, staging = _generations(tmp_path)
    (results / f"{OUTPUTS[2]}.new").write_text("newer manifest")
    (results / JOURNAL).write_text(json.dumps({"names": OUTPUTS}))
    with pytest.raises(ResultsIncomplete):
        promote(staging, results, OUTPUTS)                                # never on top of an unfinished one
    monkeypatch.setattr(pipeline, "_build_into", lambda folder: [(folder / n).write_text(f"built {n}") for n in OUTPUTS] and {"built": True})
    pipeline.build(results)
    assert _files(results) == {n: f"built {n}" for n in OUTPUTS}         # the journal was finished, then the new build published
    assert not list(results.glob(".staging_*")) and not (results / JOURNAL).exists()


def test_verify_results_refuses_a_file_the_manifest_does_not_describe(tmp_path):
    import json
    from ahah_ingest.pipeline import OUTPUTS, ResultsIncomplete, verify_results
    results = tmp_path / "results"; results.mkdir()
    (results / OUTPUTS[0]).write_bytes(b"parquet"); (results / OUTPUTS[1]).write_bytes(b"csv")
    import hashlib
    good = {"parquet": {"sha256": hashlib.sha256(b"parquet").hexdigest()}, "csv": {"file": OUTPUTS[1], "sha256": hashlib.sha256(b"csv").hexdigest(), "rows": 1}, "built_at": "x"}
    (results / "manifest.json").write_text(json.dumps(good))
    assert verify_results(results)["csv"]["rows"] == 1
    (results / OUTPUTS[1]).write_bytes(b"csv tampered")
    with pytest.raises(ResultsIncomplete, match="SHA256 differs"):
        verify_results(results)
    assert verify_results(results, files=False)["csv"]["rows"] == 1


PAUSING_BUILD = r'''
import os, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from ahah_ingest import pipeline
from ahah_ingest.pipeline import OUTPUTS
results, flags = Path(sys.argv[2]), Path(sys.argv[3])

def pause(stage):                       # tell the parent where we are, wait for its go-ahead
    (flags / f"{stage}.reached").write_text(stage)
    for _ in range(600):
        if (flags / f"{stage}.go").exists():
            return
        time.sleep(0.05)
    raise SystemExit(f"never released at {stage}")

real_write, real_replace, swapped = pipeline._write_atomic, os.replace, []
def write_atomic(path, text):
    if path.name == pipeline.JOURNAL:
        pause("before_journal")          # new files prepared beside the old ones, journal not yet written
    real_write(path, text)
def replace(src, dst):
    real_replace(src, dst)
    if str(src).endswith(".new"):
        swapped.append(dst)
        if len(swapped) == 1:
            pause("mid_swap")            # one file swapped, three still .new, journal present
pipeline._write_atomic, os.replace = write_atomic, replace
pipeline._build_into = lambda folder: [(folder / n).write_text(f"built {n}") for n in OUTPUTS] and {"built": True}
pipeline.build(results)
print("child build finished")
'''


def test_a_running_build_owns_results_and_recovery_verification_and_a_second_build_are_refused(tmp_path, monkeypatch):
    """The two overlaps of the review of 31 October: recovery while a build has prepared its
    `.new` files (it used to delete them and the build then reported success with the old
    generation), and verification while a promotion is half swapped (it used to pass on a
    mixture). Both are refused while the build owns the folder; the build then completes."""
    import shutil, subprocess, sys, time
    from ahah_ingest import pipeline
    from ahah_ingest.pipeline import OUTPUTS, ResultsBusy, recover, verify_results
    from ahah_ingest.core.sources import ROOT
    results, staging = _generations(tmp_path)
    shutil.rmtree(staging)
    flags = tmp_path / "flags"; flags.mkdir()
    child = subprocess.Popen([sys.executable, "-c", PAUSING_BUILD, str(ROOT), str(results), str(flags)],
                             stdout=subprocess.PIPE, text=True)
    monkeypatch.setattr(pipeline, "_build_into", lambda folder: pytest.fail("the second build must be refused before building"))
    try:
        for stage, expect in (("before_journal", {n: f"old {n}" for n in OUTPUTS}), ("mid_swap", None)):
            for _ in range(600):
                if (flags / f"{stage}.reached").exists():
                    break
                time.sleep(0.05)
            assert (flags / f"{stage}.reached").exists(), f"child never reached {stage}"
            with pytest.raises(ResultsBusy):
                recover(results)
            with pytest.raises(ResultsBusy):
                verify_results(results, files=False)
            with pytest.raises(ResultsBusy):
                pipeline.build(results)
            on_disk = _files(results)
            if expect:
                assert {n: on_disk[n] for n in OUTPUTS} == expect                            # the old generation untouched
                assert all((results / f"{n}.new").exists() for n in OUTPUTS)               # the prepared files not deleted
            else:
                assert (results / pipeline.JOURNAL).exists() and on_disk[OUTPUTS[0]] == f"built {OUTPUTS[0]}"
            (flags / f"{stage}.go").write_text("go")
        out, _ = child.communicate(timeout=30)
    finally:
        if child.poll() is None:
            child.kill()
    assert child.returncode == 0 and "child build finished" in out
    assert {n: _files(results)[n] for n in OUTPUTS} == {n: f"built {n}" for n in OUTPUTS}   # the new generation, whole
    assert recover(results) == "nothing to recover"


def test_ownership_is_reentrant_and_released_on_exit(tmp_path):
    from ahah_ingest.pipeline import LOCK, ResultsBusy, ResultsIncomplete, owned
    results = tmp_path / "results"; results.mkdir()
    with owned(results):
        with owned(results):                       # build -> recover -> promote nest in one process
            assert (results / LOCK).exists()
    with owned(results):
        pass                                       # released by the outer exit, not the inner one
    with pytest.raises(ResultsIncomplete, match="no manifest"):
        with owned(tmp_path / "absent"):
            pass


def test_export_csv_copies_the_verified_generation_and_refuses_a_mixture(tmp_path):
    import gzip, hashlib, json
    from ahah_ingest.pipeline import JOURNAL, OUTPUTS, ResultsIncomplete, TABLE, export_csv
    results = tmp_path / "results"; results.mkdir()
    (results / OUTPUTS[0]).write_bytes(b"parquet")
    with gzip.open(results / OUTPUTS[1], "wb") as fh:
        fh.write(b"ahah_version,datazone_code\n4,S01006506\n")
    manifest = {"parquet": {"sha256": hashlib.sha256(b"parquet").hexdigest()},
                "csv": {"file": OUTPUTS[1], "sha256": hashlib.sha256((results / OUTPUTS[1]).read_bytes()).hexdigest(), "rows": 1}, "built_at": "x"}
    (results / "manifest.json").write_text(json.dumps(manifest))
    dest = tmp_path / "out"
    assert export_csv(dest, results)["csv"]["rows"] == 1
    assert (dest / f"{TABLE}.csv").read_bytes() == b"ahah_version,datazone_code\n4,S01006506\n"
    assert json.loads((dest / "manifest.json").read_text()) == manifest
    (results / JOURNAL).write_text("{}")
    with pytest.raises(ResultsIncomplete):
        export_csv(tmp_path / "out2", results)
    assert not (tmp_path / "out2" / f"{TABLE}.csv").exists()
