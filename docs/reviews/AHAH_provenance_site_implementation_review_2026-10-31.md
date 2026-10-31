# AHAH provenance site implementation review

Date: 31 October 2026. Reviewer: Codex.

Scope: the implementation of the [approved provenance-site plan](../AHAH_Provenance_Site_Plan.md):
lineage, descriptions and document references, generated pages, build identity, tests, packaging,
and Pages publishing. Reviewed commit: `d73500975f18633649db4d244a6e247527c1c6dd`.
The working tree was clean when the review began. Implementation and repository settings were
not changed; this review is the only new repository file.

**One P1 publishing blocker and five P2 findings remain.** The local test suite, installation,
site build and link checks pass, but publication is incomplete and several provenance statements
or evidence displays need correction. The findings concern the site and its descriptions;
the absence-check finding does not mean the underlying data build omits that validation.

## Findings

### 1. P1 — Complete the GitHub Pages setup before treating publishing as working

Location: [.github/workflows/pages.yml](../../.github/workflows/pages.yml), lines 47–49;
[pages_publish.sh](../../.github/scripts/pages_publish.sh), lines 84–116; repository Pages settings.

The latest [Pages run for the reviewed commit](https://github.com/mtinti/datazone-ahah/actions/runs/41180010715)
passes installation, all 20 provenance tests, generation and MkDocs. It pushes generated commit
`847260a954e03de15f5f94cf101ed0927a34cbee` to `gh-pages`, requests a Pages build, then receives
HTTP 404 throughout polling and fails after about ten minutes. This is the current deployment
state, not an inferred future failure:

- Repository API: `has_pages: false`.
- GET `/repos/mtinti/datazone-ahah/pages`: HTTP 404.
- Public `https://mtinti.github.io/datazone-ahah/`: HTTP 404.
- The `gh-pages` branch exists at the generated commit above.

Complete the planned repository configuration for publishing from `gh-pages`, directory `/`,
then verify a successful run and public response. Creating/configuring a Pages site is a
separate operation from requesting a build; see the [GitHub Pages API documentation](https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site).
Add a preflight check with a clear setup error so an unconfigured repository does not spend the
entire polling interval returning 404. No site was enabled or workflow rerun during this review.

### 2. P2 — Cite presence checks for editions where a column must be NULL

Location: [lineage.py](../../ahah_ingest/lineage.py), lines 144–147.

The lineage adds edition checks only when the edition is in the field's `editions` list.
Consequently, `off_licence`, which is required to be NULL in 3, 4 and 5.1, cites only
`v1.presence_matrix` and `v2.presence_matrix`. Its page states the later NULL requirements but
does not cite the checks that establish them.

Reproduction: inject a failed `v3.presence_matrix` result indicating a non-NULL `off_licence`
in edition 3, then regenerate. The `off_licence` page shows **22 pass rows and no failure**;
the `GP` page shows that same edition-wide failure. The relevant failure is therefore invisible
on the page for the affected absent column.

Include each edition's `presence_matrix` check for every column, while keeping range checks and
direct source inputs conditional on actual presence. Add a regression test for an absence
violation on a column such as `off_licence` or `greenspace_active`.

### 3. P2 — Preserve reviewed corrections when rendering edition definitions

Location: [provenance_site.py](../../ahah_ingest/provenance_site.py), lines 271–273.

The edition-page renderer discards every `correction` entry and selects the first remaining
text. The generated v5.1 table consequently defines `lsoa21cd` as
`Lower Super Output Area Code (2011) / Data Zones (Scotland)`, with no correction or quotation
attribution in that row. The column page correctly retains the 2022 correction, so two routes
through the site present different definitions of the same input. The edition page's header
mentions 2022, making the contradiction visible rather than resolving it.

Render an effective reviewed definition, or keep the quotation together with its correction
and source. Preserve material qualifications when several entries apply to an edition; selecting
`defs[0]` also loses later authored qualifications. Test the generated edition page, including
the corrected Scottish geography, rather than only testing the full column page.

### 4. P2 — Correct the edition-1 definitions against the paper they cite

Location: [column_descriptions.yaml](../../ahah_ingest/column_descriptions.yaml), lines 225–248,
466–467, 1136–1146 and 1277–1282.

The new edition-scoped descriptions still contain substantive errors supported by the pinned
[Daras 2019 paper](../references/s41597-019-0114-6.pdf):

| Definition | Current site wording | Evidence and correction |
| --- | --- | --- |
| `hospital`, edition 1 | Nearest hospital, followed elsewhere by a claim that 5.1 narrows the definition to A&E hospitals and earlier editions do not say so. | Page 3 explicitly says only hospitals with A&E departments were selected; Table 3 on page 5 names A&E hospitals. Add this qualification to edition 1 and avoid claiming it originated in 5.1. Preserve uncertainty for editions whose documentation does not establish the selection rule. |
| `domain_e_exp` and `domain_e_dec`, edition 1 | Air-quality domain. | Pages 3 and 5 describe a physical-environment domain combining green space with NO2, PM10 and SO2. Split the edition-1 definition from later air-quality definitions and retain the green-space component. |
| `greenspace`, edition 1 | Green-space area within a 900-metre buffer of the area. | Page 4 describes the green-space measure available to each postcode within the buffer. Do not replace the postcode-level measurement with a buffer of the output area. |

The hospital finding also corrects **my earlier plan review**: the claim that an A&E definition
applies to 5.1 only was too strong, and the approved plan repeats it. The primary paper establishes
otherwise for edition 1. Preserve the earlier reviews as history, but correct the active plan,
descriptions and test expectations together.

The 23 entries marked as quotations from the v5 dictionary match that dictionary exactly.
The problems above concern the authored/paraphrased definitions and their edition scope.
Add source-based expectations for these edition-1 cases; coverage and reference-existence tests
cannot establish that the attributed definition is correct.

### 5. P2 — Make check explanations match the actual check's scope

Location: [provenance_site.py](../../ahah_ingest/provenance_site.py), lines 49–52 and 68–69.

The generated explanations overstate what individual checks verify:

- `header_is_mapped` is described as checking header order, but
  [reader.py](../../ahah_ingest/reader.py), lines 43–45, compares sorted names.
- `no_empty_cells` is described as checking every cell in the file, but reader lines 53–63
  check only retained Scottish rows.
- The description of every `readback.parquet.*` check bundles cells, types, nullability, key,
  rows and metadata together. A column page cites `readback.parquet.cells`, while
  [core/output.py](../../ahah_ingest/core/output.py), lines 105–125, records the other guarantees
  under separate check names.

Reproduction for the first two: a two-row CSV with header `gp,lsoa11`, a valid Scottish row,
and an empty English `gp` cell passes all seven reader checks, including the two whose generated
descriptions claim order and whole-file completeness. This is valid reader behaviour; the
documentation should describe it accurately.

Define each cited check's actual guarantee and scope. If a page presents a combined readback
guarantee, cite the complete set of checks supporting it. Add behavioural examples that test
description scope, since merely matching a check name and returning non-empty prose misses this.

### 6. P2 — Show configuration changes on the column pages that display historical passes

Location: [provenance_site.py](../../ahah_ingest/provenance_site.py), lines 152–174 and 238–240.

`evidence()` detects changed configuration hashes, but `_evidence_banner()` displays that warning
only on the home and checks pages. The column renderer calls `_checks_table()` directly, which
shows historical pass results without the changed-configuration warning.

Reproduction: change only the manifest's `registry_sha256` in a temporary copy and regenerate.
The home page correctly names the registry as changed. The direct `columns/GP/` page continues
to display current inputs alongside pass results from the historical build, with no indication
that its registry differs. Direct column links are the site's primary entry point, so the
distinction cannot depend on first visiting the home page.

Include the changed-configuration explanation and documented revision on every column page
that presents build results. A regression test should assert the warning on a column page when
registry, mapping or schema hashes differ, while retaining the historical build label.

## Smaller completion items

- **P3 — Add the planned rank/percentile guide and link it.** Only `index.md` and `checks.md`
  are generated at the site root; the plan's dedicated convention/two-scale page is absent.
  Several descriptions refer to `docs/PERCENTILES.md` as plain text. Generate the guide from
  the maintained document and link the column and decision pages to it.
- **P3 — Remove the invalid zero alternative from domain/index percentiles.** The five
  domain/index percentile descriptions say `1 (or 0) is the healthiest` despite specifying
  and enforcing the 1–100 scale. Reserve the zero lower endpoint for indicator percentiles.

## Validation and limits

| Check | Result |
| --- | --- |
| Complete local suite: `python -m pytest tests -q -rs` | **62 passed**, 14.92 seconds. |
| Suite in a source-only `git archive` snapshot, without ignored downloads or results | **56 passed, 6 expected skips**, 2.99 seconds. The earlier notebook-fixture issue is resolved. |
| Editable installation of `.[docs]` in a temporary virtual environment, using existing dependencies and no downloads | Passed; the installed module generated the site from outside the checkout. |
| Generator output | 90 column pages, 5 editions, 12 source files, 4 documents, 9 decisions; 319 distinct cited checks. |
| `mkdocs build --strict`, MkDocs 1.6.1 / Material 9.7.7 | Passed. |
| Rendered HTML links and anchors | **4,871 checked across 143 HTML files; zero broken local links/anchors**. |
| V5 dictionary quotations | All 23 compared verbatim with the pinned CSV; matched. |
| Publisher PDF evidence | Extracted the pinned documents; visually inspected paper pages 3 and 5 to verify the hospital and domain evidence. |
| Publishing-script syntax and destination generation | Passed; `feature/a` and `feature-a` produce distinct preview destinations. No publish/remove operation was invoked. |
| GitHub CI at the reviewed commit | [CI passed](https://github.com/mtinti/datazone-ahah/actions/runs/41180010760); [Pages failed during publication](https://github.com/mtinti/datazone-ahah/actions/runs/41180010715), as detailed above. |

Adversarial evidence probes used temporary copies of the manifest and generated output. Source
files, committed results, existing generated output and SQL databases were not changed. A full
data rebuild and SQL upload were not repeated: the only pipeline change in this implementation
adds build identity, and the existing data checks ran in the local suite. The saved review
records both passing checks and the gaps they did not catch.
