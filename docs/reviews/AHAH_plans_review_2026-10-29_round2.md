# AHAH plans review round 2

Date: 29 October 2026. Reviewer: Codex.

Scope: the updated [AHAH_Plan.md](../AHAH_Plan.md),
[AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), and [PERCENTILES.md](../PERCENTILES.md), checked against
the [first review](AHAH_plans_review_2026-10-29.md) and its
[response](AHAH_plans_review_2026-10-29_response.md). Supporting material remains evidence,
not a review target. The plans were not edited during this review.

Most of the first review has been addressed. Two P1 issues still prevent a faithful build,
and one P2 correction remains in the measurement descriptions.

1. **P1 — Preserve the four published v2 domain scores instead of dropping them.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 86 and 89–92, classifies `r_exp`, `h_exp`,
   `g_exp`, and `e_exp` as disposable intermediates. They are the only domain-score columns
   in the pinned v2 CSV: it has no separate `r`, `h`, `g`, or `e` score columns. For example,
   `S01006506` publishes `r_exp=0.99903726`, `h_exp=18.9438805`, `g_exp=10.75319214`, and
   `e_exp=0.983133211`. Dropping them loses four published values for every v2 zone and leaves
   no source for the v2 domain scores marked present in the matrix at lines 81–82. It also
   contradicts the main plan's promise to retain every published value. Preserve these
   columns, either as the edition's domain scores with their exponential scale documented,
   or as separate explicitly named score columns. Add a mapping/fidelity check that retains
   all four values; do not reconstruct unpublished scores from the ranks.

2. **P1 — Do not reject every numeric `-1` outside the v2 sentinel fields.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 214–215, requires any `-1` in another
   edition or column to fail. The unchanged pinned v4 CSV contains a legitimate Scottish
   domain score: `LSOA21CD=S01008132`, `ah4e=-1.0000`, `ah4e_rnk=5702`, `ah4e_pct=14`.
   Under the proposed `Decimal` parsing, `-1.0000` equals `-1`, so this rule rejects v4.
   Restrict sentinel validation to the relevant indicator and decile fields; real-valued
   domain scores must retain their valid negative values. Add this actual v4 row to the
   accepted fixtures alongside the two v2 sentinel rows.

3. **P2 — Describe v1 greenspace as an area measure, not a share.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 110–111, changes the earlier incorrect
   NDVI description to a share of area. The [v1 paper](../references/s41597-019-0114-6.pdf),
   page 4, describes an area measure of greenspace within a 900-metre buffer; it does not
   establish a proportion or percentage. The pinned Scottish data include
   `S01010824`, `gpas=277.5095373`, which is inconsistent with an ordinary fraction or
   percentage share. Use the paper's area-measure description and leave the precise area
   unit unconfirmed until the edition's documentation establishes it. Do not give the
   generated dictionary a proportion interpretation or corresponding range rule.

The earlier findings now stand as follows:

| First-review finding | Current assessment |
| --- | --- |
| 1. Incomplete schema and NULL rules | Off-licence fields, `ur`, missing v2 indicator ranks, and active-greenspace presence are addressed. Retaining the v2 domain scores remains necessary; see finding 1 above. |
| 2. Insufficient decimal scale | Addressed by `decimal(38,20)`, direct `Decimal` parsing, and fixed 20-place rendering. Every Scottish score/indicator cell round-tripped numerically in the probe. |
| 3. Unsupported reuse of SIMD types | Addressed at plan level: the required decimal and int32 extensions and Python/SQL rendering checks are explicit. The implementation still needs these extensions in its CSV, SQL, and Parquet paths. |
| 4. Unsigned decile type | The change to `smallint` addresses storage. The new blanket rejection rule needs narrowing; see finding 2 above. |
| 5. Edition-specific units | Mostly addressed: v1 distances are kilometres, v2 units are explicitly unconfirmed, and the GP medians are no longer all labelled minutes. The v1 greenspace description still needs finding 3 above. |
| 6. Inner join dropping records | Addressed by the left joins, trim/uppercase normalization, statuses, and a row-preservation test. |
| 7. Missing independent geography reference | Addressed at plan level by explicitly requiring separate Scottish Government 2011 and 2022 reference sources. Selecting and hashing the actual resources is still implementation work. |

All three smaller first-review corrections are present: GB row counts are checked before
filtering; the percentile note distinguishes 14 indicators from 15; disclosure assesses the
complete released combination and says a value can identify a zone.

The response's open questions about v2 `ur`, its units, and the exact meaning of its `-1`
codes remain open. They should remain labelled unconfirmed in generated metadata. The
implementation-order sentence at SQL-plan lines 228–230 should also acknowledge the type
extensions already described earlier, instead of saying the remaining modules are copied
with names changed.

Verification performed for this round:

- The five index CSV hashes still match those used in the first review.
- All 684,992 Scottish score and indicator cells across v1, v2, v3, v4, and v5.1 fit the
  proposed decimal precision/scale and survive text → `Decimal` → fixed 20-place text →
  `Decimal` with zero numeric mismatches. This includes the v2 domain `_exp` values and
  scientific notation in v3 and v5.1.
- Scanning exact numeric `-1` values found the 44 v2 sentinel cells and the valid v4 domain
  score reported above.
- The revised query returned all ten rows of a cohort covering matched, wrong-vintage,
  NULL, blank, whitespace-only, malformed, lower-case/padded, repeated, and internally
  spaced codes, with the expected statuses. This was a SQLite relational-logic probe with
  only SQL Server's Unicode string prefixes removed; it was not SQL Server execution.
- The v3 and v4 aggregation implementations read `NDVI_MEDIAN`, supporting the revised
  passive-greenspace description for those editions. Sources:
  [v3 aggregation](https://github.com/GeographicDataService/ahah/blob/v3/ahah/aggregate_lsoa.py)
  and [v4 aggregation](https://github.com/GeographicDataService/ahah/blob/v4/ahah/aggregate_lsoa.py).
- The percentile formulas are unchanged from the first review, which reproduced all
  published percentiles; their computation was not repeated in this round.

Document SHA256 values identify the versions reviewed here:

| Document | SHA256 |
| --- | --- |
| `docs/AHAH_Plan.md` | `a15e0daaf0649028474a1f6e2287b1068984118d6cc3281644a26f90022cd1de` |
| `docs/AHAH_SQL_Plan.md` | `827bdf999588085b679b36966af2d83501c7091bc4174c0314355f2101e675b3` |
| `docs/PERCENTILES.md` | `7a56e460d0348a822fff9c41784496c09ce6788e5ed27c4e73e524a820ccddae` |
