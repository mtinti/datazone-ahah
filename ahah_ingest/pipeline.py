"""Build the table: verify the pins, read every edition, check, write, read back, record.

    python -m ahah_ingest.pipeline            # writes results/
    python -m ahah_ingest.pipeline --verify   # results/ is one complete, accepted generation
    python -m ahah_ingest.pipeline --export D # verify, then copy manifest and CSV into D
    python -m ahah_ingest.pipeline --recover  # finish or clear an interrupted promotion
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pandas as pd

from . import checks as table_checks
from .columns import MAPPING, SCHEMA
from .core import output
from .core.checks import BuildStopped, Report
from .core.sources import ROOT, load_registry, sha256, verify
from .core import text_output as tx
from .reader import load_mapping, read_datazone_list, read_edition

PACKAGE = Path(__file__).resolve().parent
CONTRACT = PACKAGE / "export_contract.yaml"
DECISIONS = PACKAGE / "decisions.yaml"
RESULTS = ROOT / "results"
TABLE = "ahah_datazone"
OUTPUTS = [f"{TABLE}.parquet", f"{TABLE}.csv.gz", "manifest.json", "BUILD_REPORT.md"]
JOURNAL = ".promote.json"
LOCK = ".lock"


def build_identity(root: Path = ROOT) -> dict:
    """Which code built the table: the git commit, whether the tree was clean, the package and
    schema versions. Outside a repository the commit is "unknown" and dirty is None: the
    provenance site shows pass evidence only for a clean, known commit."""
    def git(*args):
        try:
            r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return r.stdout if r.returncode == 0 else None
    commit = (git("rev-parse", "HEAD") or "").strip() or "unknown"
    status = git("status", "--porcelain", "--untracked-files=no") if commit != "unknown" else None
    modified = sorted(line[3:] for line in status.splitlines() if line.strip()) if status is not None else []
    package = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    return {"commit": commit, "dirty": (bool(modified) if status is not None else None), "modified": modified,
            "package_version": package, "schema_version": output.load_schema(SCHEMA)["version"]}


class ResultsIncomplete(Exception):
    """results/ is not one complete, accepted generation."""


class ResultsBusy(ResultsIncomplete):
    """Another process owns results/ right now: a build, a recovery or a verification."""


_HELD: dict = {}      # resolved results folder -> (lock descriptor, depth), for the owning process


@contextlib.contextmanager
def owned(results: Path = RESULTS):
    """Exclusive ownership of `results` for the block: an OS lock (flock) on `results/.lock`.

    One owner at a time, across processes: a build holds it from before recovery until its
    promotion is published, recovery and verification hold it for their whole run, and a
    consumer that reads the files after verifying them holds it until it has read them. A
    second claimant is refused at once with `ResultsBusy`, never made to wait or to act on
    files another process is still using. The lock is reentrant within one process and is
    released by the kernel when the holder dies, so a killed build leaves nothing to clear."""
    results = Path(results).resolve()
    if results in _HELD:
        fd, depth = _HELD[results]
        _HELD[results] = (fd, depth + 1)
        try:
            yield
        finally:
            fd, depth = _HELD[results]
            _HELD[results] = (fd, depth - 1)
        return
    if not results.is_dir():
        raise ResultsIncomplete(f"no manifest in {results}: the folder does not exist")
    fd = os.open(results / LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            _lock(fd)
        except OSError as taken:
            raise ResultsBusy(f"{results} is owned by another process (a build, recovery or verification is running); "
                              f"try again when it has finished") from taken
        _HELD[results] = (fd, 1)
        try:
            yield
        finally:
            del _HELD[results]
            _unlock(fd)
    finally:
        os.close(fd)


try:
    import fcntl

    def _lock(fd):
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(fd):
        fcntl.flock(fd, fcntl.LOCK_UN)
except ImportError:                                   # Windows
    import msvcrt

    def _lock(fd):
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def _unlock(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


def build(results: Path = RESULTS) -> dict:
    """Build into a staging folder inside `results`, then publish the four outputs as one
    generation only after every check has passed (see `promote`). The folder is owned for the
    whole build, so no other build, recovery or verification touches it meanwhile. An
    interrupted earlier promotion is finished first, so the build never starts from a mixed
    folder."""
    results = Path(results)
    results.mkdir(parents=True, exist_ok=True)
    with owned(results):
        recover(results)
        staging = results / f".staging_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
        staging.mkdir()
        try:
            manifest = _build_into(staging)
            promote(staging, results, OUTPUTS)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    return manifest


def promote(staging: Path, results: Path, names: list) -> None:
    """Publish the outputs in `staging` as the generation in `results`.

    Four files cannot be swapped in one filesystem operation, so the protocol is journaled and
    forward-only: (1) every new file is moved into `results` under the name `<name>.new`, with
    the old files untouched; (2) the journal `.promote.json` is written atomically, naming the
    files to swap; (3) each `<name>.new` replaces `<name>` with an atomic rename; (4) the journal
    is removed. A crash before (2) leaves the old generation complete and some `.new` files,
    which `recover` deletes; a crash after (2) leaves a mixture that `recover` finishes forward,
    since every new file is already in place. Nothing is ever deleted before the new generation
    is complete, and no rollback is needed. `verify_results` refuses a folder in either
    interrupted state, so no consumer reads a mixture, and the folder is owned (see `owned`)
    throughout, so no reader hashes files while they are being swapped."""
    staging, results = Path(staging), Path(results)
    with owned(results):
        journal = results / JOURNAL
        if journal.exists():
            raise ResultsIncomplete(f"an earlier promotion is unfinished: run recover() or `python -m ahah_ingest.pipeline --recover` ({journal})")
        try:
            for name in names:
                os.replace(staging / name, results / f"{name}.new")
        except BaseException:
            for name in names:
                (results / f"{name}.new").unlink(missing_ok=True)
            raise
        _write_atomic(journal, json.dumps({"names": names, "started": dt.datetime.now(dt.timezone.utc).isoformat()}))
        try:
            _swap(results, names)
        except BaseException as error:
            raise ResultsIncomplete(f"promotion interrupted after the journal was written; nothing was deleted. "
                                    f"Finish it with `python -m ahah_ingest.pipeline --recover` ({journal}): {error!r}") from error
        journal.unlink()


def _swap(results: Path, names: list) -> None:
    for name in names:
        new = results / f"{name}.new"
        if new.exists():
            os.replace(new, results / name)


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def recover(results: Path = RESULTS) -> str:
    """Finish or clear an interrupted promotion. With a journal: swap every remaining `.new`
    file into place and remove the journal (the new generation was complete when the journal
    was written). Without one: delete stray `.new` files and staging folders; the old generation
    is complete. Refused (`ResultsBusy`) while another process owns the folder, so a running
    build's prepared files are never taken for leftovers. Returns what was done."""
    results = Path(results)
    with owned(results):
        journal = results / JOURNAL
        finished = False
        if journal.exists():
            names = json.loads(journal.read_text())["names"]
            _swap(results, names)
            journal.unlink()
            finished = True
        stray = list(results.glob("*.new")) + [p for p in results.glob(".staging_*") if p.is_dir()]
        for p in stray:
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
        (results / f"{JOURNAL}.tmp").unlink(missing_ok=True)
    if finished:
        return "finished an interrupted promotion"
    return f"removed {len(stray)} leftover(s) of an unfinished build" if stray else "nothing to recover"


def verify_results(results: Path = RESULTS, files: bool = True) -> dict:
    """The manifest of `results`, after refusing an interrupted promotion (journal or `.new`
    files present) and, with `files`, a Parquet or CSV whose SHA256 is not the manifest's.
    Every consumer of results/ reads the manifest through this. The folder is owned for the
    whole check, so the marker test, the manifest and the hashes describe one state; a
    consumer that then opens the files must do so inside its own `with owned(results)` block
    (as `export_csv` does), or the files may have been swapped since."""
    results = Path(results)
    with owned(results):
        if (results / JOURNAL).exists() or any(results.glob("*.new")):
            raise ResultsIncomplete(f"{results} holds an interrupted promotion: run `python -m ahah_ingest.pipeline --recover`")
        manifest_path = results / "manifest.json"
        if not manifest_path.is_file():
            raise ResultsIncomplete(f"no manifest in {results}")
        manifest = json.loads(manifest_path.read_text())
        if files:
            for key in ("parquet", "csv"):
                path = results / manifest[key]["file"] if key == "csv" else results / f"{TABLE}.parquet"
                if not path.is_file():
                    raise ResultsIncomplete(f"{path} is missing")
                if sha256(path) != manifest[key]["sha256"]:
                    raise ResultsIncomplete(f"{path.name} is not the file the manifest describes (SHA256 differs)")
    return manifest


def export_csv(dest: Path, results: Path = RESULTS) -> dict:
    """Verify `results` and, still owning it, copy the manifest and the uncompressed CSV into
    `dest` (`manifest.json`, `<table>.csv`). The caller then works from `dest` only, so what it
    loads is the generation that was verified. Returns the manifest."""
    import gzip
    dest, results = Path(dest), Path(results)
    dest.mkdir(parents=True, exist_ok=True)
    with owned(results):
        manifest = verify_results(results, files=True)
        with gzip.open(results / manifest["csv"]["file"], "rb") as src, open(dest / f"{TABLE}.csv", "wb") as out:
            shutil.copyfileobj(src, out)
        shutil.copyfile(results / "manifest.json", dest / "manifest.json")
    return manifest


def _build_into(results: Path) -> dict:
    report = Report()
    registry = load_registry()
    verify(registry, report)
    schema = output.load_schema(SCHEMA)
    contract = tx.load_contract(CONTRACT)
    mapping = load_mapping(MAPPING)
    decisions_sha256 = sha256(DECISIONS)

    lists = {int(v): read_datazone_list(registry.root / spec["file"], spec) for v, spec in registry.datazone_lists.items()}
    for vintage, codes in lists.items():
        report.equal(f"datazones_{vintage}.count", len(codes), registry.datazone_lists[vintage if vintage in registry.datazone_lists else str(vintage)]["zones"])
        report.equal(f"datazones_{vintage}.distinct", len(set(codes)), len(codes))
    report.require()

    parts = []
    for edition in registry.editions:
        frame = read_edition(registry.root / edition["file"], edition, mapping[edition["version"]], schema, report)
        parts.append(frame)
    table = pd.concat(parts, ignore_index=True)
    table_checks.check_table(table, schema, report)
    for edition in registry.editions:
        table_checks.check_edition(table, edition, schema, lists[int(edition["vintage"])], report)
    report.require()
    report.observe("rows_per_version", {e["version"]: int((table["ahah_version"] == e["version"]).sum()) for e in registry.editions})

    metadata = output.table_metadata(registry, schema, decisions_sha256)
    parquet = results / f"{TABLE}.parquet"
    output.write_table(table, schema, parquet, metadata)
    parquet_info = output.readback(parquet, schema, table, metadata, report)

    columns = tx.exported_columns(schema, contract, TABLE)
    rendered = tx.render(table, schema, columns, contract)
    csv_path = results / contract["tables"][TABLE]["file"]
    csv_info = tx.write_csv(rendered, contract, csv_path)
    csv_info["digest"] = tx.row_digest(rendered, contract)
    # Every byte of the CSV is ASCII: codes, version labels and numbers. Then no code page can
    # alter it on import (BULK INSERT reads the server's OEM code page unless told otherwise).
    report.equal("csv.ascii", csv_info["non_ascii_bytes"], 0, detail="no byte above 127 in the uncompressed CSV")
    tx.readback_csv(csv_path, rendered, contract, report, "readback.csv")
    # Decimal round trip: the rendered text parses back to the parsed value, for every cell.
    bad = 0
    for name in columns:
        if {f["name"]: f["type"] for f in schema["fields"]}[name] != "decimal":
            continue
        for v, text in zip(table[name], rendered[name]):
            if text != contract["digest"]["null_marker"] and tx.parse_decimal(text) != v:
                bad += 1
    report.equal("decimal_round_trip", bad, 0, detail="every decimal cell: file text, Decimal, 20-place text, Decimal")
    report.require()

    manifest = {
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "build": build_identity(),
        "table": TABLE, "schema_version": schema["version"], "schema_sha256": schema["sha256"],
        "registry_sha256": registry.sha256, "mapping_sha256": sha256(MAPPING),
        "contract_sha256": contract["sha256"], "decisions_sha256": decisions_sha256,
        "parquet": parquet_info, "csv": csv_info,
        "licence": registry.licence, "attribution": registry.attribution,
        "sources": [{"version": e["version"], "file": e["file"], "sha256": e["sha256"], "gb_rows": e["gb_rows"], "vintage": e["vintage"]} for e in registry.editions],
        "datazone_lists": {str(k): {"file": v["file"], "sha256": v["sha256"], "zones": v["zones"]} for k, v in registry.datazone_lists.items()},
        "rank_convention": output.RANK_CONVENTION,
        "summary": report.summary(), "checks": report.to_records(), "observations": report.observations,
    }
    (results / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (results / "BUILD_REPORT.md").write_text(build_report(manifest, table, rendered, registry, mapping))
    return manifest


def build_report(manifest: dict, table: pd.DataFrame, rendered: pd.DataFrame, registry, mapping: dict) -> str:
    lines = [f"# Build report: {manifest['table']}, {manifest['built_at'][:19]}Z", "",
             f"Schema `{manifest['schema_version']}`. {manifest['parquet']['rows']:,} rows by {manifest['parquet']['columns']} columns.",
             f"CSV `{manifest['csv']['file']}` SHA256 `{manifest['csv']['sha256']}`, digest total `{manifest['csv']['digest']['total']}`.", "",
             "## Rows per edition", "", "| Edition | Vintage | Rows |", "| --- | --- | --- |"]
    for e in registry.editions:
        lines.append(f"| {e['version']} | {e['vintage']} | {manifest['observations']['rows_per_version'][e['version']]:,} |")
    lines += ["", "## Checks", "", f"{manifest['summary']['blocking_passed']} passed, {manifest['summary']['blocking_failed']} failed.", "",
              "| Check | Result | Detail |", "| --- | --- | --- |"]
    for c in manifest["checks"]:
        lines.append(f"| `{c['name']}` | {'pass' if c['passed'] else 'FAIL'} | {str(c['detail'])[:120]} |")
    lines += ["", "## Three zones, cell for cell against the source file", "",
              "Version 4 (HEAL-Scot's edition) and version 5.1. The file value is the text in the pinned CSV; the table value is the CSV rendering.", ""]
    import csv as _csv
    for version, codes in (("4", ["S01006506", "S01008132"]), ("5.1", ["S01013482"])):
        e = registry.edition(version)
        with open(registry.root / e["file"], encoding="utf-8", newline="") as fh:
            reader = _csv.DictReader(fh)
            source = {r[e["code_column"]]: r for r in reader if r[e["code_column"]] in codes}
        for code in codes:
            row = rendered[(table["ahah_version"] == version) & (table["datazone_code"] == code)].iloc[0]
            lines += [f"### v{version} {code}", "", "| File column | File value | Table column | Table value |", "| --- | --- | --- | --- |"]
            for file_col, table_col in mapping[version].items():
                lines.append(f"| `{file_col}` | `{source[code][file_col]}` | `{table_col}` | `{row[table_col]}` |")
            lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(argv or [])
    if argv == ["--recover"]:
        print(recover())
        return 0
    if argv == ["--verify"] or (len(argv) == 2 and argv[0] == "--export"):
        try:
            m = verify_results() if argv == ["--verify"] else export_csv(Path(argv[1]))
        except ResultsIncomplete as problem:
            print(f"results incomplete: {problem}", file=sys.stderr)
            return 1
        print(f"results complete: {m['csv']['rows']:,} rows, built {m['built_at'][:19]}Z"
              + (f"; copied to {argv[1]}" if argv[0] == "--export" else ""))
        return 0
    try:
        manifest = build()
    except (BuildStopped, ResultsBusy) as stop:
        print(f"stopped: {stop}", file=sys.stderr)
        return 1
    print(f"built {manifest['parquet']['rows']:,} rows; {manifest['summary']['blocking_passed']} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
