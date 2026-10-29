# AHAH plans review

Date: 29 October 2026. Reviewer: Codex.

Scope: [AHAH_Plan.md](../AHAH_Plan.md), [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), and
[PERCENTILES.md](../PERCENTILES.md). The source registries, briefing, handover, issue text,
reference paper, source data, and postcode-simd implementation were supporting evidence, not
review targets. This records the review delivered in chat; the reviewed documents were not edited.

Seven issues need resolution before implementation. P1 findings prevent a faithful build or
load; P2 findings concern incorrect metadata, join behavior, or an unresolved validation source.

1. **P1 — The schema cannot preserve every edition.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 49–68, has no destination for `off` and
   `off_dec` in v1/v2, or `ur` in v2. The proposed mapping check would therefore fail.
   The NULL rules also need correction: v2 publishes no indicator ranks, and v3/v4 lack
   active-greenspace columns. Define the complete column and edition-presence matrix first.

2. **P1 — `decimal(20,16)` cannot preserve the pinned values.**
   The precision rationale in [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 91–92, confuses
   significant digits with decimal places. There are 2,621 Scottish cells in v3 and 12,106
   in v5.1 requiring more than 16 fractional digits; some need 20. For example, v5.1 publishes
   `-0.15706798766789018`. The promised check would reject these sources; an ordinary SQL
   conversion would round them. Choose precision and scale from the actual values and parse
   them without passing through floating point. See
   [SQL Server decimal rules](https://learn.microsoft.com/en-us/sql/t-sql/data-types/decimal-and-numeric-transact-sql).

3. **P1 — The SIMD exporter and SQL generator need substantive adaptation.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 18–24, promises reuse as is and no new
   check code. The current text renderer converts an unfamiliar numeric type through `int()`:
   a probe reproduced `Decimal('2.36')` becoming `"2"`. The SQL and Parquet mappings also lack
   the proposed decimal and 32-bit integer types. Digest version 1 can remain, but canonical
   decimal rendering and type support need implementation and round-trip tests. The relevant
   postcode-simd modules are `simd_ingest/core/text_output.py`, `simd_ingest/sql_check.py`, and
   `simd_ingest/core/output.py`.

4. **P1 — `tinyint` cannot store the retained `-1` deciles.**
   The indicator-decile type in [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), line 60, guarantees
   a load failure for v2 zones `S01010206` and `S01010226`. Use a signed type and
   edition-specific validation. Those rows also contain `-1` in raw indicators, so document
   that code rather than treating every non-NULL cell as an ordinary measurement. See
   [SQL Server integer ranges](https://learn.microsoft.com/en-us/sql/t-sql/data-types/int-bigint-smallint-and-tinyint-transact-sql).

5. **P2 — The shared descriptions mislabel older measurements.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), line 57, describes accessibility as minutes and
   passive greenspace as NDVI across the table. The
   [v1 paper](../references/s41597-019-0114-6.pdf), pages 1 and 4, describes kilometres and
   an area-based greenspace measure. The general warning against comparing editions does not
   fix incorrect within-edition metadata. Record units and definitions per edition, separating
   materially different concepts where necessary. The median GP values at lines 75–77 must
   not all be labelled as minutes.

6. **P2 — The join silently removes unmatched cohort records.**
   The example in [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 127–130, uses an inner join,
   contradicting the main plan's promised statuses for empty, invalid and wrong-vintage codes.
   Use a left join with the specified normalization and status logic; test that every cohort
   row survives.

7. **P2 — The independent geography reference is not already pinned.**
   [AHAH_SQL_Plan.md](../AHAH_SQL_Plan.md), lines 138–139, refers to an NRS data-zone list
   already in postcode-simd. Its current registry contains no such standalone lists.
   Identify and pin the official 2011 and 2022 lists explicitly, preserving the main plan's
   requirement that validation be independent of postcode coverage.

Three smaller corrections:

- [AHAH_Plan.md](../AHAH_Plan.md), line 132: row-count validation should explicitly check
  the GB input before filtering. The summaries contain 43,064 or 41,729/42,648 rows, not
  Scottish totals.
- [PERCENTILES.md](../PERCENTILES.md), lines 3–4: say 14 indicators in v3/v4 and 15 in v5.1.
- [AHAH_Plan.md](../AHAH_Plan.md), lines 197–201: say a released rank or value can identify
  a zone, since some ranks have ties. Assess the complete released combination, including
  SIMD and multiple editions where applicable.

All 15 registered source hashes matched. Recomputing every published percentile in v3, v4
and v5.1 produced zero mismatches, supporting the policy of retaining the published scales.
SQL Server itself was not exercised; these findings concern the plans, pinned data, and
the existing Python implementation proposed for reuse.
