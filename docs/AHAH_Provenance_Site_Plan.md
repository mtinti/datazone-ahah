# Plan: a column provenance site on GitHub Pages

Drafted 31 October 2026, after the SIMD site (`postcode-simd`, `docs/plans/Column_Provenance_Site_Plan.md`
there); revised the same day after review (build identity, edition-scoped descriptions, document
references, the presence check, the blue and green space expectations). Status: proposed.

## Aim

A public site at `https://mtinti.github.io/datazone-ahah/`, regenerated on every push to `main`, with
**one page per column** of `ahah_datazone`. A link such as `.../columns/domain_h_dec/` shows what the
column is, which file column of which edition feeds it, what was done to it, how the build checks it,
why, and how it is exported. Metadata only: no data values, nothing not already public.

## What exists

AHAH is a simpler case than SIMD. Most of what the SIMD plan had to build is already committed here:

| Fact | Where it lives |
| --- | --- |
| name, type, nullability, group, editions, description | `output_schema.yaml` (all 90 descriptions are filled) |
| the exact source field, per edition | `mapping.yaml`: every file column of every edition maps to exactly one table column, so the lineage is already a tested file, not something to derive from reader code |
| which columns an edition has | the presence matrix in `columns.py`, checked once per edition by `v<ed>.presence_matrix` (all 90 columns together; there is no per-column presence check) |
| the pinned files: publisher, URL, SHA256, licence, DOI | `sources.yaml`; `data/sources/*/SOURCES.md` |
| the transformation | the readers: text copied, Decimal parsed, GB rows filtered to S01 codes; no value is changed |
| the checks | `manifest.json["checks"]`, 341 names: per column `v<ed>.<column>.range`; per edition `v<ed>.presence_matrix`, `v<ed>.gb_rows`, `v<ed>.header_is_mapped`, `v<ed>.no_empty_cells`, `v<ed>.every_zone_of_<vintage>_present_once` and the rest; `source.<path>`, `readback.*`, `table.*` |
| the reasons | `decisions.yaml`, 9 entries with ids |
| units and edition notes | `UNITS` in `dictionary.py` |
| the export | `export_contract.yaml`, `sql_check.py` (SQL type per column, the digest) |
| the publisher's own definitions | `dictionary_ahah_v5.csv` (23 variables) and the v5 methodology PDF, both hashed in `data/sources/geods/SOURCES.md` but not in the registry `load_registry` reads; the Daras 2019 paper, committed in `docs/references/` |

Missing, in four parts:

- a per-column record that joins these;
- a description source with attribution: today a column's description is ours, typed into
  `columns.py`, and the site should say which words are the publisher's and which are ours;
- a **build identity**: the manifest records `built_at` and the hashes of the artefacts, registry,
  schema, mapping, contract and decisions, but not the code revision that ran the checks. The
  committed manifest's `registry_sha256` already differs from the current `sources.yaml` (the Zenodo
  DOI was added after the build), which is a documentation change, not a data change, and shows why
  the site must separate current documentation from historical build evidence;
- machine-readable references for the documents the descriptions quote (section 3).

## Design

### 1. Pages

- **One page per column**, 90. Sections: *What it is* (the short description, type, nullability,
  group, which editions carry it, then the edition-scoped definitions and units of section 3);
  *Where it comes from* (one row per edition: the file column, the pinned file, its SHA256,
  publisher page, licence); *What was done to it* (copied as text; Decimal; S01 filter; NULL where
  the edition lacks it); *How it is checked* (the check names and what each tests, with the
  edition-wide checks marked as such); *Why* (decision links); *Export* (CSV column, SQL Server
  type, part of the digest).
- **Index pages**: columns grouped as the data dictionary groups them (key, index, domains,
  indicators, deciles, percentiles), with the edition presence matrix; one page per edition listing
  its file, its columns and the ones it lacks; one page per pinned file; one page per decision;
  one page defining the checks; a page on the rank convention and the two percentile scales.
- Cross-links throughout, as on the SIMD site.

### 2. The lineage map

`ahah_ingest/lineage.py` returns one record per column, built from `mapping.yaml`, the presence
matrix, the registry, `sql_check.py` and the check names, never typed by hand. A record holds
per-edition inputs (file, SHA256, field, join key `datazone_code`), the transformation kind
(`copied_text`, `decimal`, `int`, `key`, `derived` for `ahah_version` and `datazone_vintage`), the
checks that guard it, the decision ids, and the SQL export.

Checks are cited by **exact name**, each with its scope. A column's record names its own
`v<ed>.<column>.range` for each edition that has it, and the edition-wide checks that cover it:
`v<ed>.presence_matrix` (the column is present or absent exactly as the matrix says),
`v<ed>.header_is_mapped`, `v<ed>.no_empty_cells`, `v<ed>.every_zone_of_<vintage>_present_once`,
and for the routed indicators of edition 2 `v2.no_route_code_zones` and
`v2.no_route_code_outside_routed`. A name that is not in the committed manifest's check set fails
the test; a pattern match is not enough.

### 3. Descriptions with attribution

A committed `ahah_ingest/column_descriptions.yaml`, one entry per column. The schema descriptions
stay the short form. An entry holds one or more **edition-scoped** definitions, each with the
editions it applies to, the text, the unit, and a reference, because definitions change between
editions: `GP` is a network distance in kilometres in edition 1 and a drive time in minutes from
edition 3; `greenspace` is an area measure in edition 1 and median NDVI from edition 3; `hospital`
means one with an accident and emergency department in 5.1 only; edition 2's units are unconfirmed
and stay so. A quotation is marked as a quotation and a project-authored explanation as ours. A
reviewed correction can sit beside a quotation: the v5 dictionary calls the code column "(2011)"
while the methodology report, section 2.2, and the zone count say 2022 data zones. A suffix
description (`_dec`, `_pct`, `_rnk`) is shared where its meaning is identical.

References are machine-readable through a small **document registry**, `ahah_ingest/documents.yaml`,
committed and usable in Pages CI without the ignored downloads. Reference kinds:

- `pinned_document`: the v5 dictionary and the methodology PDF, with the path and SHA256 already
  recorded in `data/sources/geods/SOURCES.md`, and a location (row, or section and page);
- `repository_document`: the 2019 paper under `docs/references/`, with its SHA256 and DOI;
- `ours`: project-authored, pointing at a decision id or a repository file where one applies.

The coverage test requires every column to have an entry covering every edition that carries it,
every `pinned_document` or `repository_document` reference to resolve in the document registry
with its hash, and allows `ours` without an external file.

### 4. Generation and publishing

- `python -m ahah_ingest.provenance_site` writes Markdown to `build/provenance_docs`; MkDocs with the
  Material theme renders it (a `docs` extra in `pyproject.toml`, never needed by the build).
- `.github/workflows/pages.yml` and `.github/scripts/pages_publish.sh` copied from SIMD: tests
  first, then generate, build, push to `gh-pages`, wait for the Pages build; branch previews under
  `preview/`; pull requests build only. Pages enabled in the repository settings on `gh-pages`.
- The site states the commit it documents, the package version and the schema version, and,
  separately, the identity of the build whose check evidence it shows (section 5, choice 1).

### 5. Open choices

1. **Check evidence.** The SIMD site states only what a check tests. Here `results/manifest.json` is
   committed, so a page could also say that a check passed, but the manifest does not say which
   code revision ran it. Recommendation, in two steps. First, the pipeline records a build identity
   in the manifest: the git commit (`unknown` outside a repository), whether the tree was clean
   (`dirty: true` with the list of modified tracked files otherwise), the package version and the
   schema version. Second, the site shows pass evidence only from a manifest with a clean, known
   commit, labelled with that commit and `built_at`, never with the site's own commit; a manifest
   without identity, or a dirty one, yields check definitions only, with the recorded `built_at` and
   artefact hashes shown as the evidence's identity and the revision marked unknown. A
   configuration hash that differs from the current file (today the registry) is shown as "changed
   since this build", by name. Tests: a manifest without identity never acquires the current
   commit; a dirty manifest shows no pass label; a changed registry hash is reported, not hidden.
2. **The HEAL-Scot twelve.** A page listing the v4 columns the project asked for would be useful,
   but the release form is undecided. Recommendation: leave it out until decided.
3. **Build statistics per column** (nulls, min, max per edition). The manifest's `observations`
   holds only rows per edition, and the range checks record bounds, not observed values, so the
   pipeline would first have to write these statistics. Recommendation: phase 2, with that as its
   prerequisite.

## Tests (`tests/test_provenance.py`)

- Every schema column has a lineage record and a description entry covering every edition that
  carries it; every document reference resolves in the document registry with its hash; an `ours`
  reference needs no external file.
- Edition-scoped descriptions: `GP` (kilometres in 1, minutes from 3), `greenspace` (area in 1,
  NDVI from 3), `hospital` (A&E definition in 5.1 only), `datazone_code` (the "(2011)" quotation with
  the 2022 correction), and the unconfirmed edition 2 wording is preserved.
- Every input field is in `mapping.yaml` for that edition and only for editions where the presence
  matrix says the column is present; absent editions have no input.
- Every check name a page cites is a member of the committed manifest's check set, by exact name;
  every column cites its own range check for each edition that has it and the edition-wide checks
  that cover it; every decision id exists.
- Build identity: a manifest without identity never acquires the site's commit; a dirty build shows
  no pass label; a changed configuration hash is named.
- Hand-stated expectations: `off_licence` has inputs for editions 1 and 2 only; `domain_h_exp` for
  1 and 2, `domain_h` for 3 onward; `ur` for 2 only; `bluespace` for 2, 3, 4 and 5.1 (`blue`, `blue`,
  `ah4blue`, `bluespace`); `greenspace_active` for 2 and 5.1 (`gact`, `greenspace_active`); the rank,
  percentile and decile variants of each follow the presence matrix for their group, stated
  separately; `datazone_code` reads `lsoa11`, `lsoa11`, `lsoa11`, `LSOA21CD`, `lsoa21cd`.
- The generator writes 90 column pages, every internal link resolves, `mkdocs build --strict` passes.

## Out of scope

Data values, the HEAL-Scot release shape, anything under `local/`.

## Effort

One and a half days: the lineage map and tests are small because `mapping.yaml` already is the
lineage; the build identity, the document registry, the edition-scoped descriptions and the copied
workflow take most of it.
