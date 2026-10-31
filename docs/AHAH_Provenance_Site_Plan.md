# Plan: a column provenance site on GitHub Pages

Drafted 31 October 2026, after the SIMD site (`postcode-simd`, `docs/plans/Column_Provenance_Site_Plan.md`
there). Status: proposed.

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
| which columns an edition has | the presence matrix in `columns.py`, checked per edition by `v<ed>.<column>.absent` and `.present` |
| the pinned files: publisher, URL, SHA256, licence, DOI | `sources.yaml`; `data/sources/*/SOURCES.md` |
| the transformation | the readers: text copied, Decimal parsed, GB rows filtered to S01 codes; no value is changed |
| the checks | `manifest.json["checks"]`, 341 names of the form `v<ed>.<column>.range`, `v<ed>.gb_rows`, `source.<path>`, `readback.*`, `table.*` |
| the reasons | `decisions.yaml`, 9 entries with ids |
| units and edition notes | `UNITS` in `dictionary.py` |
| the export | `export_contract.yaml`, `sql_check.py` (SQL type per column, the digest) |
| the publisher's own definitions | `dictionary_ahah_v5.csv` (23 variables), the v5 methodology PDF, the Daras 2019 paper in `docs/references/` |

Missing: a per-column record that joins these, and a description source with attribution. Today a
column's description is ours, typed into `columns.py`; the site should say which are the publisher's
words and which are ours.

## Design

### 1. Pages

- **One page per column**, 90. Sections: *What it is* (description, type, nullability, group, unit,
  which editions carry it); *Where it comes from* (one row per edition: the file column, the pinned
  file, its SHA256, publisher page, licence); *What was done to it* (copied as text; Decimal; S01
  filter; NULL where the edition lacks it); *How it is checked* (the check names and what each
  tests); *Why* (decision links); *Export* (CSV column, SQL Server type, part of the digest).
- **Index pages**: columns grouped as the data dictionary groups them (key, index, domains,
  indicators, deciles, percentiles), with the edition presence matrix; one page per edition listing
  its file, its columns and the ones it lacks; one page per pinned file; one page per decision;
  one page defining the checks; a page on the rank convention and the two percentile scales.
- Cross-links throughout, as on the SIMD site.

### 2. The lineage map

`ahah_ingest/lineage.py` returns one record per column, built from `mapping.yaml`, the presence
matrix, the registry, `sql_check.py` and the check-name patterns, never typed by hand. A record holds
per-edition inputs (file, SHA256, field, join key `datazone_code`), the transformation kind
(`copied_text`, `decimal`, `int`, `key`, `derived` for `ahah_version` and `datazone_vintage`), the
checks that guard it, the decision ids, and the SQL export.

### 3. Descriptions with attribution

A committed `ahah_ingest/column_descriptions.yaml`, one entry per column, with the text and its
source: the v5 dictionary (file and SHA256) where it defines the variable, the methodology PDF or the
2019 paper where it defines a domain or an older indicator (`off_licence`, `so2`), and ours otherwise,
marked as ours. The schema descriptions stay the short form. A column without an entry fails the test.

### 4. Generation and publishing

- `python -m ahah_ingest.provenance_site` writes Markdown to `build/provenance_docs`; MkDocs with the
  Material theme renders it (a `docs` extra in `pyproject.toml`, never needed by the build).
- `.github/workflows/pages.yml` and `.github/scripts/pages_publish.sh` copied from SIMD: tests
  first, then generate, build, push to `gh-pages`, wait for the Pages build; branch previews under
  `preview/`; pull requests build only. Pages enabled in the repository settings on `gh-pages`.
- The site states the commit, the package version, the schema version and the release the check
  evidence comes from.

### 5. Open choices

1. **Check evidence.** The SIMD site states only what a check tests. Here `results/manifest.json` is
   committed, so a page can also say "passed in build `<commit>`, 341 of 341". Recommendation: show
   it, bound to the manifest's build commit, not to the current one.
2. **The HEAL-Scot twelve.** A page listing the v4 columns the project asked for would be useful,
   but the release form is undecided. Recommendation: leave it out until decided.
3. **Build statistics per column** (nulls, min, max per edition). The ranges are already checked;
   the values would come from the manifest. Recommendation: phase 2.

## Tests (`tests/test_provenance.py`)

- Every schema column has a lineage record and a description; every description source names a
  pinned file that is in the registry.
- Every input field is in `mapping.yaml` for that edition and only for editions where the presence
  matrix says the column is present; absent editions have no input.
- Every check name a page cites matches a pattern the build emits, verified against the committed
  manifest; every decision id exists.
- Hand-stated expectations: `off_licence` has inputs for editions 1 and 2 only; `domain_h_exp` for
  1 and 2, `domain_h` for 3 onward; `ur` for 2 only; `bluespace` and `greenspace_active` for 5.1 only;
  `datazone_code` reads `lsoa11`, `lsoa11`, `lsoa11`, `LSOA21CD`, `lsoa21cd`.
- The generator writes 90 column pages, every internal link resolves, `mkdocs build --strict` passes.

## Out of scope

Data values, the HEAL-Scot release shape, anything under `local/`.

## Effort

One day: the lineage map and tests are small because `mapping.yaml` already is the lineage; the
descriptions file and the copied workflow take most of it.
