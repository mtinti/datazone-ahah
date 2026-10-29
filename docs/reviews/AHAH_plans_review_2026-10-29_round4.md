# AHAH plans review round 4

Date: 29 October 2026. Reviewer: Codex.

Scope: the latest [AHAH_Plan.md](../AHAH_Plan.md),
[AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), and [PERCENTILES.md](../PERCENTILES.md), checked
against [round 3](AHAH_plans_review_2026-10-29_round3.md) and its
[response](AHAH_plans_review_2026-10-29_round3_response.md). Supporting files remain
evidence rather than review targets. The plans were not edited.

No remaining P1 or P2 findings. Both round-3 findings are resolved, and the plans are ready
for implementation. This closes the previous substantive findings at plan level; it does
not establish that an AHAH implementation or SQL Server load has passed its tests.

| Round-3 finding | Resolution and verification |
| --- | --- |
| P1: nullable `ur` could lose NULLs in the boolean writers | SQL-plan line 123 uses nullable `tinyint` restricted to 0/1 for v2 and NULL elsewhere. This uses the existing nullable-integer path. A probe of the actual copied renderer produced the null marker, `0`, and `1`; the actual Arrow conversion preserved `[None, 0, 1]`. Line 242 specifies the CSV, Parquet, digest, and SQL round trip and rejection of invalid v2 values. |
| P2: v1 exponential domain values were labelled as probit scores | SQL-plan lines 83–85 and 96–110 now put v1 and v2 values into the exponential columns, leave the probit columns NULL for both editions, leave `domain_g_exp` NULL for v1, and retain the v1 environment-domain definition. Line 241 requires source fidelity and the corresponding NULL pattern. Published values remain unchanged. |

The older-edition column description at SQL-plan lines 63–65 now lists the groups rather
than retaining the incorrect fixed count of three columns.

One minor documentation cleanup remains after the newly recorded HEAL-Scot decision:

- **P3 — Synchronize the remaining edition-choice wording and examples.** The main plan
  records v4 as decided at lines 56–59 and 235, but its work-order item at line 225 and the
  SQL plan's item at line 253 still describe choosing an edition as pending. Mark those
  items settled. The example at SQL-plan lines 199–209 is explicitly a valid v5.1/2022-zone
  example; retain that label and add a v4/2011-zone example for the HEAL-Scot workflow, or
  make v4 the primary worked example. This does not block the build, which still carries
  all five editions.

The new HEAL-Scot column list was checked against the pinned v4 file: all twelve columns
exist. Its overall rank is unique for all 6,976 Scottish zones, and also for all 42,648
GB rows, supporting the added disclosure statement. The recorded project decision itself
was taken as context from the updated plan; the meeting record was not independently read.

Verification for this round:

- Read the complete updated main and SQL plans. The percentile document is byte-identical
  to the previously reviewed version.
- Exercised `simd_ingest/core/text_output.py::render` with a nullable `int8` field and
  `{NULL, 0, 1}`; the output was `{NUL marker, "0", "1"}`. Exercised the actual
  `simd_ingest/core/output.py::_column` function for the same field; its Arrow array
  preserved `{NULL, 0, 1}`.
- Confirmed that the published v2 `ur` values are exactly `0` and `1` across the GB file.
  The v2 and v4 index hashes still match the earlier reviewed sources.
- Checked the revised domain mapping and fidelity requirements against the evidence from
  round 3. The decimal and percentile computations and unchanged join logic were not
  rerun; their previous results remain recorded in the earlier reviews.

Implementation still needs the independent geography-source pins, generated schema and
mapping files, decimal/int32 writer extensions, and the planned SQL Server integration
checks. Historical units and inferred flag/code meanings should keep their documented
qualifications. These are implementation tasks rather than additional review findings.

Document SHA256 values identify the versions reviewed here:

| Document | SHA256 |
| --- | --- |
| `docs/AHAH_Plan.md` | `05713531716497147e394710a60383beb6e1729323dfb1c02dc94630e4404fec` |
| `docs/AHAH_SQL_Plan.md` | `91a134a5b27ab6ec57ea673c469640d19cc3b64dd28a9d434862c0f2d8056893` |
| `docs/PERCENTILES.md` | `7a56e460d0348a822fff9c41784496c09ce6788e5ed27c4e73e524a820ccddae` |
