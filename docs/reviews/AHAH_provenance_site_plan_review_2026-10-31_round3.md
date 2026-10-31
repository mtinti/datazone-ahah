# AHAH provenance site plan review, round 3

Date: 31 October 2026. Reviewer: Codex.

Scope: the updated [provenance site plan](../AHAH_Provenance_Site_Plan.md), checked against
[round 2](AHAH_provenance_site_plan_review_2026-10-31_round2.md) and its
[response](AHAH_provenance_site_plan_review_2026-10-31_round2_response.md). The plan and
implementation were not edited.

Reviewed commit: `69d05eba6d459a7477d17c1045ac4883c25701a2`.
Plan SHA256: `098280f70fae89d722e55c668892b4410f7cfce136461ec134a35f2055523c97`.

**No remaining P1 or P2 findings. The plan is ready for implementation.** This closes the
previously raised plan findings; it does not establish that the proposed site or publishing
workflow has been implemented or tested.

The round-2 range-check finding is resolved in both places:

- Lines 69–76 require a range reference only where the build emits one, derive applicability
  from the build rules, and explicitly identify the keys, overall score and probit domains as
  exceptions. Exact manifest membership remains required.
- Lines 149–152 give corresponding test expectations: keys, `ahah` and probit domain scores
  have no range reference, while applicable indicator, rank and exponential-domain ranges
  remain required. The former contradictory universal requirement is gone.

The five round-1 resolutions remain intact: correct edition presence, historical build
identity, edition-scoped descriptions, resolvable document references with an authored-text
exception, and the actual edition-wide presence check. The statistics prerequisite also
remains explicit.

Verification for this round:

- Read the complete revised plan and response and inspected the commit diff. Only the plan
  and review documents changed; the implementation, schema, mapping and manifest did not.
- Compared schema presence with the manifest's exact check names: **273 present column/edition
  pairs, 241 range checks, 32 pairs without ranges**, with no range names outside the present
  pairs.
- Confirmed that all three keys, `ahah` and all four probit domains have no range references
  in their present editions. Confirmed positive examples `v4.GP.range`, `v4.GP_rnk.range`,
  `v1.domain_h_exp.range` and `v2.domain_g_exp.range`.
- The ten build-rule tests passed in round 1 and were not rerun for this documentation-only
  change. No site generation, link validation, MkDocs build or deployment was performed;
  those checks belong to the forthcoming implementation.
