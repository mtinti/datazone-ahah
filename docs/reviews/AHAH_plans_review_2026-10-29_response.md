# Response to the plans review of 29 October 2026

Every finding was re-checked against the files before the plans were changed. All seven hold.

| Finding | Verified how | Resolution in the plans |
| --- | --- | --- |
| 1. Schema cannot hold every edition | Headers of the five files: `off`, `off_dec` in v1 and v2, `ur` and four `_exp` in v2, no `gact` in v1, v3, v4, no indicator ranks in v1 and v2, no `blue` and no green domain in v1 | `AHAH_SQL_Plan.md`, "The table": a column-by-edition matrix, three columns for older editions only (`off_licence`, `ur`, `_dec`), the v2 `_exp` intermediates mapped to "dropped", and the mapping check both ways |
| 2. decimal(20,16) loses values | Counted fractional digits in Scottish rows: up to 20; 12,106 cells of v5.1 and 2,621 of v3 exceed 16; v3 uses scientific notation | `decimal(38,20)`, parsed with `Decimal` and never through a float, canonical fixed rendering with 20 decimals on both sides, round-trip tests |
| 3. Exporter and SQL generator need new types | `text_output.py` line 76 renders any other number with `int()` | The modules are copied and extended with `decimal` and `int32`, each with one rendering in Python and SQL and a round-trip test. Digest version stays 1 |
| 4. tinyint cannot hold `-1` | v2 rows `S01010206` and `S01010226` have `-1` in eleven raw indicators and eleven deciles | Deciles are `smallint`; `-1` allowed only in those columns of v2, described as the edition's code; a `-1` anywhere else fails |
| 5. Units mislabelled for older editions | Daras et al. 2019: network distance in kilometres, green space as area within a buffer | Units recorded per edition in the data dictionary; v2 units marked unconfirmed; the median GP values no longer all called minutes |
| 6. Inner join drops cohort rows | Read | Left join with trim and upper case, four statuses, and a test that every input row returns once |
| 7. No pinned data zone list | `sources.yaml` of postcode-simd has no standalone zone list | The 2011 and 2022 Scottish Government lists are pinned as sources of their own |

The three smaller corrections are applied: the row-count check runs on the whole file before the
Scottish filter, `PERCENTILES.md` says 14 indicators in v3 and v4 and 15 in v5.1, and the
disclosure section says a value "can" identify a zone and that the whole released combination is
what is assessed.

Not done, and still open: the meaning of v2's `ur` column and of its `-1` code, which need the
version 2 documentation that is not held.
