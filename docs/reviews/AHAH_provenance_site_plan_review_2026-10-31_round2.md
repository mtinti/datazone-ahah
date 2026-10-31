# AHAH provenance site plan review, round 2

Date: 31 October 2026. Reviewer: Codex.

Scope: the updated [provenance site plan](../AHAH_Provenance_Site_Plan.md), compared with the
[first review](AHAH_provenance_site_plan_review_2026-10-31.md) and its
[response](AHAH_provenance_site_plan_review_2026-10-31_response.md). Supporting implementation
and metadata were checked as evidence. The plan and implementation were not edited.

Reviewed commit: `40cb69aafcd037e445df32633805dc94ed9448b5`.
Plan SHA256: `d5c94e95a83a69378096f3458544008353b35ef47a8129e0869c7836f88af8b0`.

The five original findings are addressed at plan level. One new P2 remains in the revised
check-coverage requirement; narrow it before implementation. No P1 finding.

## Finding

### P2 — Require range checks only for column/edition pairs the build range-checks

Location: plan lines 142–144; the same requirement appears at lines 68–69.

The revised test requires every column to cite its own range check for each edition carrying
it, while also requiring every cited check to exist in the manifest. Those requirements cannot
both hold for the current build. The schema has **273 present column/edition pairs**, but the
manifest contains **241 per-column range checks**. The remaining 32 pairs are:

| Columns | Editions | Pairs without a `.range` check |
| --- | --- | --- |
| `ahah_version`, `datazone_vintage`, `datazone_code` | 1, 2, 3, 4, 5.1 | 15 |
| `domain_h`, `domain_g`, `domain_e`, `domain_r` | 3, 4, 5.1 | 12 |
| `ahah` | 1, 2, 3, 4, 5.1 | 5 |

For example, `v4.domain_h.range` and `v4.ahah.range` do not exist. The condition branches in
[checks.py](../../ahah_ingest/checks.py), lines 49–73, emit ranges for ranks, percentiles,
deciles, `ur`, indicators and exponential domain scores. They emit none for the columns above.
Those columns still have relevant presence, table, geography, parsing or readback protections.

Change the requirement to: **each column cites every applicable range check actually emitted
for that column and edition, plus the other checks that cover it**. Determine applicability
from the build's rules and verify the resulting exact names against the manifest. Add explicit
expectations that a key, a probit domain score and `ahah` have no invented `.range` reference,
while an indicator, a rank and an exponential domain score retain their applicable ranges.
Otherwise a correct generator will fail the proposed acceptance test, or the site will claim
checks that never ran.

## Resolution of the previous review

| Previous finding | Resolution in the updated plan |
| --- | --- |
| 1. Incorrect blue/green-space edition expectations | Lines 147–151 give the correct raw-indicator inputs and require suffix variants to follow their own presence groups. The current schema confirms these sets. |
| 2. Missing build identity | Lines 36–40 acknowledge the existing manifest's limits. Lines 113–124 add actual build identity, clean/dirty handling, historical labelling, a fallback for missing identity, and visible configuration-hash differences, with tests. This closes the plan gap; the pipeline change is still to be implemented. |
| 3. Descriptions need edition scope | Lines 78–87 specify edition-scoped text, units and references, preserve v2 uncertainty, and distinguish quotations, authored explanations and corrections. Lines 137–139 name the exceptional cases to test. |
| 4. Description references do not resolve | Lines 89–99 add a committed document registry, distinguish pinned and repository documents from authored text, and require resolution by hash without ignored downloads in CI. |
| 5. Invented per-column presence checks | Lines 22 and 68–74 now use the real edition-wide `presence_matrix` check and exact manifest membership. This fixes the original presence-check issue; the newly added universal range requirement is the finding above. |
| Smaller statistics correction | Lines 127–130 acknowledge that observed per-column statistics must first be generated and recorded by the pipeline. |

## Verification and limits

- Read the complete revised plan and response, and compared the changes with the previous
  revision. The update changes only the plan and review documents; implementation, schemas,
  mappings and manifest are unchanged.
- Enumerated all present `(edition, column)` pairs from `output_schema.yaml` and compared their
  exact candidate range names with all 341 committed manifest checks: 241 range names match,
  32 present pairs have no range check, and no emitted range names fall outside the present
  pairs. Confirmed the reason by reading `check_edition`.
- Rechecked all five `presence_matrix` names and the blue/green-space variants. `bluespace`
  ranks/percentiles exist in 3, 4 and 5.1, and its decile in 2; `greenspace_active`
  ranks/percentiles exist in 5.1, and its decile in 2.
- The ten build-rule tests passed in the preceding review. They were not rerun for this
  documentation-only update. No provenance generator, site test or deployment exists yet to
  execute; this review establishes plan corrections, not implementation or publishing success.
