# Response to the provenance site plan review, round 2 (31 October 2026)

Review: [AHAH_provenance_site_plan_review_2026-10-31_round2.md](AHAH_provenance_site_plan_review_2026-10-31_round2.md).
Plan: [AHAH_Provenance_Site_Plan.md](../AHAH_Provenance_Site_Plan.md).

**P2, range checks required where none is emitted.** Reproduced: the schema has 273 present column
and edition pairs and the manifest 241 `v<ed>.<column>.range` names; the 32 pairs without one are
the three key columns, `ahah` and the four probit domain scores, which the branches of
`check_edition` do not range-check. The plan now says a column cites its range check only for the
editions in which the build emits one, that applicability is derived from the same rules the build
uses and verified against the manifest by exact name, and the tests state that a key column, `ahah`
and a probit domain score cite no range check while an indicator, a rank and an exponential domain
score cite theirs.

The reviewer's resolution table for round 1 matches the plan; nothing further changed.

My findings on the review are closed.
