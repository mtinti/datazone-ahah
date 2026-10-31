# Response to the provenance site plan review of 31 October 2026

Review: [AHAH_provenance_site_plan_review_2026-10-31.md](AHAH_provenance_site_plan_review_2026-10-31.md).
Every finding was reproduced against the files before the plan was changed. The plan is
[AHAH_Provenance_Site_Plan.md](../AHAH_Provenance_Site_Plan.md); no implementation exists yet.

| # | Finding | Reproduced | Plan change |
| --- | --- | --- | --- |
| 1 | `bluespace` and `greenspace_active` are not 5.1-only | yes: `mapping.yaml` gives `bluespace` inputs in 2, 3, 4, 5.1 (`blue`, `blue`, `ah4blue`, `bluespace`) and `greenspace_active` in 2 and 5.1 (`gact`, `greenspace_active`) | the hand-stated expectations now list these sets, with the rank, percentile and decile variants stated separately per the presence matrix |
| 2 | no build identity in the manifest | yes: the manifest's keys are `built_at` and hashes, no commit or version; its `registry_sha256` `6b23d95a…` differs from the current `sources.yaml` `42e9f0bb…` (the Zenodo DOI line added after the build) | new task: the pipeline records commit, dirty flag with modified files, package and schema version; the site shows pass evidence only from a clean, known build, labelled with that commit, never its own; a manifest without identity or a dirty one yields definitions only with the revision marked unknown; a changed configuration hash is named; three tests added |
| 3 | one description per column misdescribes earlier editions | yes: `UNITS` in `dictionary.py` already separates v1 kilometres and area measure, v3 minutes and NDVI, the 5.1 hospital definition, and the unconfirmed v2 units | descriptions are edition-scoped entries with text, unit and reference; quotations are marked; a reviewed correction can sit beside a quotation (the "(2011)" label against the 2022 zones); suffix descriptions shared only where identical; tests name `GP`, `greenspace`, `hospital`, `datazone_code` and the v2 wording |
| 4 | the dictionary, methodology and paper are not in the registry; `ours` cannot meet an external-file rule | yes: `sources.yaml` has no document entries; the two GeoDS documents are hashed only in `SOURCES.md`; the paper is in `docs/references/` | a committed document registry, `documents.yaml`, with kinds `pinned_document`, `repository_document` and `ours`; the coverage test resolves the first two by hash and exempts `ours`; works in Pages CI without the downloads |
| 5 | no per-column presence checks exist | yes: the manifest has five `v<ed>.presence_matrix` records and no `.present` or `.absent` names | the table and the lineage section cite the edition-wide check by exact name with its scope; a cited name must be a member of the manifest's check set, a pattern match is not enough; each column must cite its own range checks and the edition-wide checks covering it |
| small | phase 2 statistics assume values the manifest lacks | yes: `observations` holds only `rows_per_version` | writing the statistics in the pipeline is now phase 2's prerequisite |

Effort revised from one day to one and a half.

My findings on the review are closed: each of the five points held against the files and none needed
narrowing.
