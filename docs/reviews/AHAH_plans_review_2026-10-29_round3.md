# AHAH plans review round 3

Date: 29 October 2026. Reviewer: Codex.

Scope: the latest [AHAH_Plan.md](../AHAH_Plan.md),
[AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), and [PERCENTILES.md](../PERCENTILES.md), including
the changes responding to [round 2](AHAH_plans_review_2026-10-29_round2.md) and its
[response](AHAH_plans_review_2026-10-29_round2_response.md). Supporting sources were used as
evidence. The reviewed plans were not edited.

All three round-2 findings are addressed. The latest plan has one P1 finding arising from
the new `ur` bit type and one P2 finding in the newly explicit distinction between
domain-score scales.

1. **P1 — Add nullable-boolean support for the new `ur` bit column.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 77 and 113, now makes `ur` a SQL `bit`
   present only in v2. The copied SIMD writers do not support nullable booleans: the `bool`
   branch of `simd_ingest/core/text_output.py`, lines 62–63, calls `bool(v)` without checking
   for missing values, and `simd_ingest/core/output.py`, lines 86–87, casts the entire series
   to boolean. A probe of the actual text renderer converted `None` to `"0"`, converted
   floating NaN to `"1"`, and raised a `TypeError` for pandas `NA`; the Parquet conversion
   has the same loss of missingness or fails. This affects the 28,320 rows outside v2,
   where the presence matrix requires `ur` to be NULL. Extending only `decimal` and `int32`,
   as the implementation plan currently specifies, does not fix this existing boolean path.

   Add an explicit nullable-boolean change to both writers, preserving the digest's null
   marker, the empty CSV field, the Parquet null, and SQL NULL. Add a `{NULL, 0, 1}`
   round-trip fixture and an edition-presence assertion for `ur`. Alternatively, retain
   `ur` as a nullable integer restricted to 0/1 if boolean storage is unnecessary. Neither
   alternative changes the published 0/1 values or establishes what the flag means.

2. **P2 — Apply the domain-scale distinction to v1 as well as v2.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 81–83 and 94–100, puts only v2 in
   `domain_<x>_exp`, keeps v1 `h`, `e`, and `r` in the ordinary domain columns, and describes
   those ordinary columns as being on the probit scale. The v1 values are also exponentially
   transformed domain scores. For `S01006506`, the pinned file publishes `h=35.34476733`,
   `e=0.786943857`, and `r=1.032016388`; Scottish `h` and `r` reach 100. The
   [v1 source code](https://github.com/GDSL-UL/AHAH/blob/27b20672388d380dc0141714c01ba95ee6d5af86/create_index_v1.R#L88-L123)
   constructs domain scores, ranks them, and applies the exponential transformation. As an
   independent numeric check, all 41,729 published values in each of the three v1 domain
   columns invert to integer ranks within 0.000006, consistent with their published rounding.
   The current split therefore leaves v1 mislabelled even when an analyst uses only that
   edition; the warning against comparisons between editions does not correct the metadata.

   Prefer mapping v1 `h`, `e`, and `r` into `domain_h_exp`, `domain_e_exp`, and `domain_r_exp`
   too, with `domain_g_exp` NULL for v1. Update the presence matrix and fidelity checks
   accordingly. If retaining mixed scales in the ordinary columns is intentional instead,
   explicitly document v1's exponential scale and remove the unqualified probit description.
   In either design, keep the published values unchanged. The per-edition definition should
   also preserve the fact that v1's environment domain includes greenspace as well as air
   pollutants, as shown in the same source code.

The previous round's findings are closed at plan level:

| Round-2 finding | Resolution in the current SQL plan |
| --- | --- |
| Preserve the four v2 domain scores | Lines 83 and 94–100 retain all four values in named `_exp` columns. Lines 90–92 forbid dropped source columns, and line 231 requires fidelity for every v2 zone. The separate v1 scale issue is recorded above. |
| Accept the valid v4 domain score of `-1` | Lines 130–138 distinguish indicator/decile sentinel codes from real domain scores. Lines 228–230 explicitly accept `S01008132` and restrict the rejection rule to the relevant fields and editions. |
| Correct the v1 greenspace description | Lines 118–121 describe an area measure within a 900-metre buffer, leave the area unit unconfirmed, and avoid treating it as a proportion. |

The implementation order at lines 244–247 now explicitly includes extending the CSV writer,
Parquet writer, and SQL generator with `decimal` and `int32`. That resolves the earlier
wording inconsistency about merely changing names. The newly selected nullable `bit` also
requires the change in finding 1.

Minor editorial cleanup: line 63 still says that three columns exist only for older editions.
The schema now includes the older decile columns and four exponential-score columns as well
as the off-licence fields and `ur`; replace that fixed count with a description of the groups.

The acknowledged implementation tasks remain: select and pin the independent geography
reference resources, retain unconfirmed historical units and inferred code meanings as such,
and execute the generated import and digest checks on SQL Server. These are planned work,
not additional findings in this review.

Verification for this round:

- The five index CSV hashes match the files used in the preceding reviews.
- The main plan and percentile note are byte-identical to round 2; only the SQL plan changed
  among the three review targets.
- Checked the revised v2 mapping, sentinel-validation rules, accepted fixtures, and v1
  greenspace wording against the source evidence already established in round 2.
- Exercised the existing SIMD boolean renderer and the Parquet boolean-conversion expression
  with object `None`, nullable-boolean `NA`, and floating NaN, alongside 0/1 values. The
  results establish the nullable-boolean gap described in finding 1. This new type decision
  was checked after rereading the plan's latest saved version.
- Fetched the original v1 build code at commit
  `27b20672388d380dc0141714c01ba95ee6d5af86` and checked the domain transformations. For
  `n=41729` and published domain value `x`, the inverse transformation
  `n * (1 - exp(-x/23)) / (1 - exp(-100/23))` is within
  `5.886051440029405e-06` of an integer for every published v1 `h`, `e`, and `r` value.
  This is evidence about the score scale, not a proposal to derive or publish missing ranks.
- The unchanged decimal rendering, join query, and percentile formulas retain the evidence
  recorded in the earlier reviews. Those probes were not repeated. No SQL Server execution
  or end-to-end AHAH build was performed.

Document SHA256 values identify the versions reviewed here:

| Document | SHA256 |
| --- | --- |
| `docs/AHAH_Plan.md` | `a15e0daaf0649028474a1f6e2287b1068984118d6cc3281644a26f90022cd1de` |
| `docs/AHAH_SQL_Plan.md` | `a070191453cce9256802ab91eecbf0a914a984accadc6669a367bec8cc456056` |
| `docs/PERCENTILES.md` | `7a56e460d0348a822fff9c41784496c09ce6788e5ed27c4e73e524a820ccddae` |
