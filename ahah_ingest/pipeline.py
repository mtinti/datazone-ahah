"""Build the table: verify the pins, read every edition, check, write, read back, record.

    python -m ahah_ingest.pipeline            # writes results/
"""

from __future__ import annotations

import datetime as dt
import json
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


def build(results: Path = RESULTS) -> dict:
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

    results.mkdir(parents=True, exist_ok=True)
    metadata = output.table_metadata(registry, schema, decisions_sha256)
    parquet = results / f"{TABLE}.parquet"
    output.write_table(table, schema, parquet, metadata)
    parquet_info = output.readback(parquet, schema, table, metadata, report)

    columns = tx.exported_columns(schema, contract, TABLE)
    rendered = tx.render(table, schema, columns, contract)
    csv_path = results / contract["tables"][TABLE]["file"]
    csv_info = tx.write_csv(rendered, contract, csv_path)
    csv_info["digest"] = tx.row_digest(rendered, contract)
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
    try:
        manifest = build()
    except BuildStopped as stop:
        print(f"stopped: {stop}", file=sys.stderr)
        return 1
    print(f"built {manifest['parquet']['rows']:,} rows; {manifest['summary']['blocking_passed']} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
