"""Write the column provenance site as Markdown, for MkDocs (docs/AHAH_Provenance_Site_Plan.md).

    python -m ahah_ingest.provenance_site [out_dir]      # default build/provenance_docs

One page per column, per edition, per pinned file, per document and per decision, and a page
defining the build's checks. Everything comes from the committed schema, mapping, registry,
documents, descriptions, decisions, export contract and the lineage map. Pass evidence comes
from the committed manifest only when it records a clean, known build commit; otherwise the
pages show what each check tests and nothing more. No data values.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

import yaml

from .columns import MAPPING, SCHEMA, VERSIONS
from .core import output
from .core import text_output as tx
from .core.sources import load_registry, sha256
from .lineage import PACKAGE, ROOT, lineage
from .pipeline import CONTRACT, DECISIONS, JOURNAL

MANIFEST = ROOT / "results" / "manifest.json"
SITE_NAME = "datazone-ahah column provenance"
REPOSITORY = "https://github.com/mtinti/datazone-ahah/blob/main/"
GROUP_TITLE = {"key": "key columns", "indicator": "indicators (raw values)", "ur": "the version 2 urban flag",
               "indicator_rnk": "indicator ranks", "indicator_pct": "indicator percentiles", "indicator_dec": "indicator deciles",
               "domain": "domain scores (probit, editions 3 onward)", "domain_exp": "domain scores (exponential, editions 1 and 2)",
               "domain_rnk": "domain ranks", "domain_pct": "domain percentiles", "domain_dec": "domain deciles",
               "ahah": "the overall index score", "ahah_rnk": "the overall rank", "ahah_pct": "the overall percentile",
               "ahah_dec": "the overall decile"}
KIND_LABEL = {"quotation": "quoted from", "paraphrase": "paraphrased from", "correction": "reviewed correction, evidence",
              "ours": "our wording"}

# What each kind of check tests. Every check a page cites must match one of these (tested), and
# must also be a member of the manifest's check set by exact name (tested).
CHECKS = [
    (r"^source\.", "the pinned file is present and its SHA256 equals the registry's: the bytes are exactly the ones reviewed"),
    (r"^datazones_\d{4}\.count$", "the pinned data zone list has the declared number of zones"),
    (r"^datazones_\d{4}\.distinct$", "no zone is repeated in the pinned data zone list"),
    (r"^v[\d.]+\.header_is_mapped$", "the set of header names equals the set of mapped file columns: an added, dropped or renamed column stops the build (order is not checked; the mapping is by name)"),
    (r"^v[\d.]+\.header_unique$", "no file column name is repeated"),
    (r"^v[\d.]+\.row_width$", "every row has exactly as many cells as the header"),
    (r"^v[\d.]+\.no_empty_cells$", "no cell of a Scottish row (code starting S01) is empty: every value the table takes is present; rows of England and Wales are not checked"),
    (r"^v[\d.]+\.gb_rows$", "the file has the number of Great Britain rows the publisher's data summary states"),
    (r"^v[\d.]+\.scottish_rows$", "the Scottish rows (codes starting S01) number exactly the data zones of the vintage"),
    (r"^v[\d.]+\.scottish_code_shape$", "every Scottish code is S01 followed by six digits"),
    (r"^v[\d.]+\.scottish_codes_distinct$", "no Scottish code is repeated within the edition"),
    (r"^v[\d.]+\.every_zone_of_\d{4}_present_once$", "the edition's codes equal the pinned data zone list of its vintage: every zone once, none missing, none extra"),
    (r"^v[\d.]+\.vintage$", "every row of the edition carries the edition's vintage"),
    (r"^v[\d.]+\.presence_matrix$", "across all 90 columns, a cell is NULL exactly where the presence matrix says the edition has no such column, and never otherwise"),
    (r"^v[\d.]+\.ahah_rnk_unique$", "the overall rank is unique within the edition: it identifies the data zone"),
    (r"^v[\d.]+\.[A-Za-z0-9_]+\.range$", "every non-null value of the column is within its declared range for the edition"),
    (r"^v2\.no_route_code_zones$", "the version 2 value -1 occurs in routed indicators and their deciles only in the two known zones"),
    (r"^v2\.no_route_code_outside_routed$", "the value -1 occurs in no non-routed indicator or decile of version 2"),
    (r"^v[\d.]+\.no_minus_one_code$", "the value -1 occurs in no routed indicator or decile of this edition"),
    (r"^table\.columns$", "the assembled table has exactly the schema's columns, in order"),
    (r"^table\.key_unique$", "the key (ahah_version, datazone_code) is unique"),
    (r"^table\.required_nonnull$", "no non-nullable column holds a NULL"),
    (r"^readback\.parquet\.column_names$", "the saved Parquet file's column names equal the schema's, in order"),
    (r"^readback\.parquet\.column_types$", "the saved Parquet file's Arrow types equal the schema's (decimal128(38,20), int8, int16, int32, string)"),
    (r"^readback\.parquet\.nullability$", "the saved Parquet file's nullability flags equal the schema's"),
    (r"^readback\.parquet\.rows$", "the saved Parquet file, re-read, has as many rows as the accepted table"),
    (r"^readback\.parquet\.primary_key_unique$", "the key is unique in the re-read Parquet file"),
    (r"^readback\.parquet\.cells$", "every cell of the re-read Parquet file equals the accepted table's, null for null and value for value"),
    (r"^readback\.parquet\.metadata\.", "the saved Parquet file carries the named metadata key with the expected value"),
    (r"^readback\.csv\.header$", "the written CSV's header equals the exported column list"),
    (r"^readback\.csv\.rows$", "the written CSV, re-read, has as many rows as the rendered table"),
    (r"^readback\.csv\.cells$", "every cell of the re-read CSV equals the rendered text, byte for byte"),
    (r"^decimal_round_trip$", "every decimal cell's 20-place text parses back to the parsed value"),
    (r"^csv\.ascii$", "every byte of the uncompressed CSV is ASCII, so no import code page can alter a value"),
]


def describe_check(name: str) -> str | None:
    return next((text for pattern, text in CHECKS if re.search(pattern, name)), None)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")


def _version() -> dict:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    package = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    return {"commit": r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "unknown", "package": package,
            "schema": yaml.safe_load(SCHEMA.read_text())["version"]}


def evidence(manifest: dict | None, root: Path = ROOT) -> dict:
    """What the committed manifest may be cited for. Pass evidence only from a clean, known build
    commit; a manifest without identity, or from a dirty tree, yields definitions only. The
    configuration hashes are compared with the current files and any difference is named."""
    if manifest is None:
        return {"usable": False, "reason": "no build manifest is committed", "results": {}, "changed": [], "identity": None}
    if (MANIFEST.parent / JOURNAL).exists() or any(MANIFEST.parent.glob("*.new")):
        return {"usable": False, "reason": "results/ holds an interrupted promotion: the manifest may not describe the files beside it", "results": {}, "changed": [], "identity": None}
    identity = manifest.get("build")
    current = {"schema": output.load_schema(SCHEMA)["sha256"], "registry": load_registry(PACKAGE / "sources.yaml").sha256,
               "mapping": sha256(MAPPING), "contract": tx.load_contract(CONTRACT)["sha256"], "decisions": sha256(DECISIONS)}
    changed = [k for k, v in current.items() if manifest.get(f"{k}_sha256") != v]
    base = {"identity": identity, "built_at": manifest.get("built_at", "")[:19] + "Z", "changed": changed,
            "results": {c["name"]: bool(c["passed"]) for c in manifest.get("checks", [])},
            "summary": manifest.get("summary", {})}
    if not identity:
        return base | {"usable": False, "reason": "the manifest records no build identity (an older pipeline wrote it): the code revision that ran the checks is unknown"}
    if identity.get("commit", "unknown") == "unknown":
        return base | {"usable": False, "reason": "the build ran outside a git repository: the code revision is unknown"}
    if identity.get("dirty") is not False:
        return base | {"usable": False, "reason": f"the build ran on a tree with uncommitted changes ({', '.join(identity.get('modified') or ['unknown files'])}): the committed revision is not the code that ran"}
    return base | {"usable": True, "reason": "", "label": f"build `{identity['commit'][:7]}` ({base['built_at']}, package {identity.get('package_version')}, schema `{identity.get('schema_version')}`)"}


def _evidence_banner(ev: dict) -> list:
    if ev["usable"]:
        lines = [f"**Check evidence:** {ev['label']}: {ev['summary'].get('blocking_passed', '?')} checks passed, "
                 f"{ev['summary'].get('blocking_failed', '?')} failed. Each column page shows that build's result for every check it cites."]
    else:
        lines = [f"**Check evidence:** none shown. {ev['reason'].capitalize()}. The pages state what each check tests, not that it passed."]
        if ev.get("identity") is None and ev.get("built_at"):
            lines.append(f"The committed manifest was built {ev['built_at']}; its artefact hashes identify the output, not the code.")
    if ev.get("changed"):
        lines.append("**Changed since that build:** " + ", ".join(f"`{c}`" for c in ev["changed"]) +
                     ". The build evidence describes the previous version of these files; the pages describe the current one.")
    return lines + [""]


def _description_block(entries: list, documents: dict, lines: list, decisions_known: set) -> None:
    lines += ["| Editions | Definition | Unit | Source |", "| --- | --- | --- | --- |"]
    for e in entries:
        ref = e["reference"]
        if "document" in ref:
            doc = documents[ref["document"]]
            src = f"{KIND_LABEL[e['kind']]} [{doc['title'].split('.')[0] if e['kind'] != 'correction' else doc['title']}](../documents/{ref['document']}.md), {ref['location']}"
            if e["kind"] == "correction":
                src = f"{KIND_LABEL[e['kind']]}: [{doc['title']}](../documents/{ref['document']}.md), {ref['location']}"
        else:
            src = KIND_LABEL["ours"]
            if ref.get("decision"):
                src += f", decision [`{ref['decision']}`](../decisions/{ref['decision']}.md)"
        text = _link_docs(e["text"] if e["kind"] != "quotation" else f"“{e['text']}”")
        lines.append(f"| {', '.join(e['editions'])} | {text} | {e.get('unit') or ''} | {src} |")
    lines.append("")


def _result(ev: dict, names: list) -> str:
    """One word for a group of checks in the evidenced build: pass if every one passed, else
    the failing or missing names."""
    bad = [n for n in names if ev["results"].get(n) is not True]
    if not bad:
        return "pass"
    return "; ".join(f"`{n}`: {'FAIL' if ev['results'].get(n) is False else 'not in this build'}" for n in bad)


def _checks_table(checks: list, ev: dict) -> list:
    """The column's checks grouped by kind: a per-edition check (v<ed>.x) is one row listing the
    editions it runs in, so a page reads as a dozen rows, not sixty. Every name stays exact in
    the markup (the `names` column) so the citation can be verified against the manifest."""
    groups: dict = {}
    for name, scope in checks:
        m = re.match(r"^v([\d.]+)\.(.+)$", name)
        key = (m.group(2), scope) if m else (name, scope)
        groups.setdefault(key, {"editions": [], "names": []})
        if m:
            groups[key]["editions"].append(m.group(1))
        groups[key]["names"].append(name)
    head = "| Check | Scope | Editions | What it tests |" + (" Result |" if ev["usable"] else "")
    lines = [f"Result from {ev['label']}." if ev["usable"] else "What each check tests. No build result is shown: " + ev["reason"] + ".", "",
             head, "| --- | --- | --- | --- |" + (" --- |" if ev["usable"] else "")]
    for (kind, scope), g in groups.items():
        label = f"`v<ed>.{kind}`" if g["editions"] else f"`{kind}`"
        if g["editions"]:
            label += " <!-- " + " ".join(g["names"]) + " -->"
        row = f"| {label} | {scope} | {', '.join(g['editions']) or 'all'} | {describe_check(g['names'][0])} |"
        if ev["usable"]:
            row += f" {_result(ev, g['names'])} |"
        lines.append(row)
    return lines + [""]


def _link_docs(text: str) -> str:
    return text.replace("docs/PERCENTILES.md", "[Ranks and percentiles](../conventions.md)")


def _edition_definition(entries: list, edition: str, documents: dict) -> str:
    """Every definition that applies to the edition, in order, each marked by kind: a quotation
    stays with its correction and any qualification, so the edition page never shows a quoted
    wording the review has corrected without the correction beside it."""
    parts = []
    for e in entries:
        if edition not in e["editions"]:
            continue
        if e["kind"] == "quotation":
            parts.append(f"“{e['text']}” (quoted, [{documents[e['reference']['document']]['title'].split('.')[0]}](../documents/{e['reference']['document']}.md))")
        elif e["kind"] == "correction":
            parts.append(f"**Correction:** {e['text']}")
        elif e["kind"] == "paraphrase":
            parts.append(f"{e['text']} (after [{documents[e['reference']['document']]['title'].split('.')[0]}](../documents/{e['reference']['document']}.md))")
        else:
            parts.append(e["text"])
    return _link_docs(" ".join(parts))


def write(out: Path) -> dict:
    """Write every page, then remove any page in `out` this run did not write."""
    out = Path(out)
    for sub in ("columns", "sources", "documents", "decisions", "editions"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    before = set(out.rglob("*.md"))
    counts = _write_pages(out)
    written = {out / p for p in counts.pop("_written")}
    for stale in sorted(before - written):
        stale.unlink()
    return counts


def _write_pages(out: Path) -> dict:
    written = []

    def emit(path: Path, text: str) -> None:
        path.write_text(text)
        written.append(path.relative_to(out))

    version = _version()
    registry = load_registry(PACKAGE / "sources.yaml")
    schema = yaml.safe_load(SCHEMA.read_text())
    fields = {f["name"]: f for f in schema["fields"]}
    mapping = yaml.safe_load(MAPPING.read_text())["editions"]
    documents = yaml.safe_load((PACKAGE / "documents.yaml").read_text())["documents"]
    descriptions = yaml.safe_load((PACKAGE / "column_descriptions.yaml").read_text())["columns"]
    decisions = {d["id"]: d for d in yaml.safe_load(DECISIONS.read_text())["decisions"]}
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else None
    ev = evidence(manifest)
    L = lineage()
    names = list(fields)
    by_file, by_decision, by_document = defaultdict(set), defaultdict(set), defaultdict(set)
    for name, r in L.items():
        for i in r["inputs"]:
            if i["kind"] == "pinned_file":
                by_file[i["path"]].add(name)
        for d in r["decisions"]:
            by_decision[d].add(name)
        for e in descriptions[name]:
            if "document" in e["reference"]:
                by_document[e["reference"]["document"]].add(name)
            if e["reference"].get("decision"):
                by_decision[e["reference"]["decision"]].add(name)

    for name in names:
        f, r = fields[name], L[name]
        lines = [f"# `{name}`", "", _link_docs(f["description"]), "",
                 f"**Type:** {f['type']} (SQL Server `{r['export']['sql_type']}`). **Nullable:** {'yes' if f['nullable'] else 'no'}. "
                 f"**Group:** [{GROUP_TITLE[f['group']]}](group-{f['group']}.md). **Editions:** " +
                 ", ".join(f"[{v}](../editions/{v}.md)" for v in f["editions"]) +
                 (f"; NULL in {', '.join(r['absent'])}" if r["absent"] else "") + ".", "",
                 "## What it is, by edition", ""]
        _description_block(descriptions[name], documents, lines, set(decisions))
        lines += ["## Where it comes from", "", "| Edition | File column | Pinned file | SHA256 | Reaches the row by |", "| --- | --- | --- | --- | --- |"]
        for i in r["inputs"]:
            if i["kind"] == "pinned_file":
                lines.append(f"| {i['edition']} | `{i['field']}` | [`{i['path']}`](../sources/{_slug(i['path'])}.md) | `{i['sha256'][:12]}…` | {i['join'] or 'it is the key'} |")
            else:
                lines.append(f"| {i['edition']} | `{i['field']}` of the edition | `{i['path']}` (registry) | | written on every row |")
        lines += ["", f"**What was done to it:** *{r['transformation']['kind']}*. {r['transformation']['rule']} (code: `{r['transformation']['code']}`)", "",
                  "## How it is checked", ""]
        lines += _checks_table(r["checks"], ev)
        if ev.get("changed"):
            lines += ["**Changed since that build:** " + ", ".join(f"`{c}`" for c in ev["changed"]) +
                      ". The results above come from the build named; the inputs and definitions on this page describe the current files.", ""]
        lines += ["", "## Why", ""] + [f"- [`{d}`](../decisions/{d}.md): {decisions[d]['decision']}" for d in r["decisions"]] + [""]
        lines += ["## Export", "", f"CSV column `{r['export']['csv_column']}`, in every row of `ahah_datazone.csv.gz`; SQL Server type "
                  f"`{r['export']['sql_type']}`; part of the row digest (`docs/sql/check_loaded_digest.sql`). An absent value is an empty cell and NULL.", ""]
        emit(out / "columns" / f"{name}.md", "\n".join(lines))

    # Column index by group, with the presence matrix.
    lines = ["# Columns", "", f"{len(names)} columns of `ahah_datazone`, schema `{schema['version']}`, key `ahah_version`, `datazone_code`. "
             "A dot marks the editions that publish the column; elsewhere it is NULL.", ""]
    for g, title in GROUP_TITLE.items():
        members = [n for n in names if fields[n]["group"] == g]
        if not members:
            continue
        lines += [f"## {title[0].upper() + title[1:]}", "", "| Column | " + " | ".join(f"v{v}" for v in VERSIONS) + " |", "| --- |" + " --- |" * len(VERSIONS)]
        lines += [f"| [`{n}`]({n}.md) | " + " | ".join("●" if v in fields[n]["editions"] else "" for v in VERSIONS) + " |" for n in members]
        lines.append("")
        page = [f"# {title[0].upper() + title[1:]}", "", f"{len(members)} columns.", "", "| Column | Editions | Description |", "| --- | --- | --- |"]
        page += [f"| [`{n}`]({n}.md) | {', '.join(fields[n]['editions'])} | {fields[n]['description']} |" for n in members]
        emit(out / "columns" / f"group-{g}.md", "\n".join(page))
    emit(out / "columns" / "index.md", "\n".join(lines))

    # Editions.
    lines = ["# Editions", "", "| Edition | Year | Vintage | File | Columns | Not published |", "| --- | --- | --- | --- | --- | --- |"]
    for ed in registry.editions:
        v = ed["version"]
        has = [n for n in names if v in fields[n]["editions"]]
        lacks = [n for n in names if v not in fields[n]["editions"]]
        lines.append(f"| [{v}]({v}.md) | {ed['year']} | {ed['vintage']} | [`{ed['file']}`](../sources/{_slug(ed['file'])}.md) | {len(has)} | {len(lacks)} |")
        page = [f"# AHAH version {v}", "", f"Published {ed['year']}, on the {ed['vintage']} Scottish data zones. File [`{ed['file']}`](../sources/{_slug(ed['file'])}.md), "
                f"SHA256 `{ed['sha256']}`, {ed['gb_rows']:,} Great Britain rows, code column `{ed['code_column']}`.", "",
                "## Columns this edition publishes", "", "| File column | Table column | Definition in this edition |", "| --- | --- | --- |"]
        for file_col, table_col in mapping[v].items():
            page.append(f"| `{file_col}` | [`{table_col}`](../columns/{table_col}.md) | {_edition_definition(descriptions[table_col], v, documents)} |")
        page += ["", "## Columns NULL in this edition", "", ", ".join(f"[`{n}`](../columns/{n}.md)" for n in lacks) or "none", ""]
        emit(out / "editions" / f"{v}.md", "\n".join(page))
    emit(out / "editions" / "index.md", "\n".join(lines))

    # Sources: one page per pinned file.
    pins = []
    for ed in registry.editions:
        pins += [(ed["file"], ed["sha256"], f"edition {ed['version']} index file", "geods" if ed["file"].startswith("geods/") else "geods_previous"),
                 (ed["summary"], ed["summary_sha256"], f"edition {ed['version']} data summary (the publisher's per-column counts, the source of the Great Britain row count)", "geods" if ed["summary"].startswith("geods/") else "geods_previous")]
    for vintage, spec in registry.datazone_lists.items():
        pins.append((spec["file"], spec["sha256"], f"{vintage} data zone list ({spec['zones']:,} zones), from {spec['page']}", "datazones"))
    lines = ["# Pinned sources", "", f"Every file the build reads, {len(pins)} files, pinned by SHA256: a changed byte stops the build. "
             f"{registry.licence}. Archived copy of the whole set: Zenodo DOI `{yaml.safe_load((PACKAGE / 'sources.yaml').read_text()).get('zenodo_sources_doi', '')}`.", "",
             "| File | Role | Columns fed |", "| --- | --- | --- |"]
    for path, digest, role, folder in pins:
        fed = sorted(by_file.get(path, ()))
        lines.append(f"| [`{path}`]({_slug(path)}.md) | {role} | {len(fed)} |")
        page = [f"# `{path}`", "", f"**Role:** {role}.", "", f"**SHA256:** `{digest}`.", "",
                f"**Publisher page:** <{registry.publisher_pages.get(folder, registry.datazone_lists.get(str(path.split('/')[0]), {}).get('page', ''))}>" if folder != "datazones" else f"**Publisher page:** <{[s for s in registry.datazone_lists.values() if s['file'] == path][0]['page']}>", "",
                f"**Licence:** {registry.licence}.", "",
                f"**Columns it feeds ({len(fed)}):** " + (", ".join(f"[`{n}`](../columns/{n}.md)" for n in fed) or "none directly (a count or a reference list the checks compare against)"), ""]
        emit(out / "sources" / f"{_slug(path)}.md", "\n".join(page))
    lines += ["", "## Attribution", ""] + [f"- {a}" for a in registry.attribution]
    emit(out / "sources" / "index.md", "\n".join(lines))

    # Documents the descriptions quote.
    lines = ["# Documents", "", "The publisher's definitions the column pages quote or paraphrase, each with the hash of the copy read.", "",
             "| Document | Kind | Columns citing it |", "| --- | --- | --- |"]
    for did, d in documents.items():
        cites = sorted(by_document.get(did, ()))
        lines.append(f"| [{d['title']}]({did}.md) | {d['kind'].replace('_', ' ')} | {len(cites)} |")
        page = [f"# {d['title']}", "", f"**Kind:** {d['kind'].replace('_', ' ')}. **Applies to edition(s):** {', '.join(d['applies_to'])}.", "",
                f"**File:** `{d['path']}`, SHA256 `{d['sha256']}`." + (" Committed in this repository." if d["kind"] == "repository_document" else " A pinned download, hashed in the source record, not committed."), ""]
        for key, label in (("publisher", "Publisher"), ("page", "Page"), ("doi", "DOI"), ("licence", "Licence")):
            if d.get(key):
                page.append(f"**{label}:** {('<' + d[key] + '>') if key == 'page' else d[key]}.")
        page += ["", f"**Columns citing it ({len(cites)}):** " + ", ".join(f"[`{n}`](../columns/{n}.md)" for n in cites), ""]
        emit(out / "documents" / f"{did}.md", "\n".join(page))
    emit(out / "documents" / "index.md", "\n".join(lines))

    # Decisions.
    lines = ["# Decisions", "", "The decision log (`ahah_ingest/decisions.yaml`): what was decided and why. Its SHA256 travels in the Parquet metadata and the manifest.", "",
             "| Decision | Date | Columns governed |", "| --- | --- | --- |"]
    for did, d in decisions.items():
        gov = sorted(by_decision.get(did, ()))
        lines.append(f"| [`{did}`]({did}.md) | {d['date']} | {len(gov)} |")
        page = [f"# `{did}`", "", f"**Date:** {d['date']}.", "", f"**Decision.** {d['decision']}", "", f"**Why.** {d['why']}", "",
                f"**Columns ({len(gov)}):** " + (", ".join(f"[`{n}`](../columns/{n}.md)" for n in gov) or "none directly"), ""]
        emit(out / "decisions" / f"{did}.md", "\n".join(page))
    emit(out / "decisions" / "index.md", "\n".join(lines))

    # Conventions: the rank direction and the two percentile scales, from the maintained document.
    percentiles = (ROOT / "docs" / "PERCENTILES.md").read_text()
    emit(out / "conventions.md", "\n".join([
        "# Ranks and percentiles", "", output.RANK_CONVENTION, "",
        "Every `_rnk` column is a rank over Great Britain with 1 the healthiest; every `_dec` column a decile 1 to 10 with 1 the healthiest. "
        "The percentiles come in two scales, as the document below (maintained as `docs/PERCENTILES.md` in the repository) explains. "
        "Decision: [`percentile-scales`](decisions/percentile-scales.md); [`ranks-gb-only`](decisions/ranks-gb-only.md).", "",
        re.sub(r"^# ", "## ", percentiles, count=1, flags=re.M)]))

    # Checks.
    used = sorted({c for r in L.values() for c, _ in r["checks"]})
    lines = ["# Checks", "", "What each build check tests. A column page lists the checks that guard it by exact name and scope."]
    lines += _evidence_banner(ev)
    lines += ["| Kind of check | What it tests | Cited names |", "| --- | --- | --- |"]
    for pattern, text in CHECKS:
        n = sum(1 for c in used if re.search(pattern, c))
        lines.append(f"| `{pattern}` | {text} | {n} |")
    emit(out / "checks.md", "\n".join(lines))

    home = [f"# {SITE_NAME}", "",
            "For every column of `ahah_datazone`, the table of the Access to Healthy Assets and Hazards index for Scottish data zones: "
            "what it is in each edition, which file column feeds it, what was done to it, how the build checks it, why, and how it is exported.", "",
            f"Generated from commit `{version['commit']}`: package {version['package']}, schema `{version['schema']}`. Metadata only: no data values.", ""]
    home += _evidence_banner(ev)
    home += ["- [Columns](columns/index.md): one page per column, with the presence matrix",
             "- [Editions](editions/index.md): one page per AHAH edition, its file and its columns",
             "- [Pinned sources](sources/index.md): every file the build reads, by SHA256",
             "- [Documents](documents/index.md): the publisher's definitions the pages quote",
             "- [Decisions](decisions/index.md): why each column is made the way it is",
             "- [Checks](checks.md): what each build check tests",
             "- [Ranks and percentiles](conventions.md): the direction of every rank and the two percentile scales", "",
             f"{output.RANK_CONVENTION}", ""]
    emit(out / "index.md", "\n".join(home))
    return {"columns": len(names), "editions": len(registry.editions), "sources": len(pins), "documents": len(documents),
            "decisions": len(decisions), "checks": len(used), "evidence": ev["usable"], "_written": written}


def main(argv=None) -> int:
    out = Path(argv[0]) if argv else ROOT / "build" / "provenance_docs"
    print(write(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
