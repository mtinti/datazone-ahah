# Plan: shape the AHAH table for SQL Server

Status: proposed, 29 October 2026. Companion to `AHAH_Plan.md`, which covers the sources, the
checks and the choice of version. This document covers only the shape of the output and how it
reaches SQL Server. It copies the path that postcode-simd already walks, so that the same
loader, the same check script and the same review steps apply.

Every edition's files were downloaded on 29 October 2026 and are listed with their hashes in
`data/sources/geods/SOURCES.md` and `data/sources/geods_previous/SOURCES.md`. The columns
below are those of the version 5.1 file.

## What postcode-simd does, and what AHAH reuses

| Step | postcode-simd | AHAH |
| --- | --- | --- |
| Declare the columns | `simd_ingest/output_schema_history.yaml`: name, type, nullable, key, description | `ahah_ingest/output_schema.yaml`, same format, one table |
| Decide what the CSV carries | `simd_ingest/export_contract.yaml`: which columns go out, in which order | `ahah_ingest/export_contract.yaml`. Every column goes out; AHAH has no coordinates to withhold |
| Write the CSV | `core/text_output.py`: UTF-8, one rendering per type, refuses NCHAR(0) and NCHAR(31) in text | extended with two types, `decimal` and `int32`, see below |
| Record the build | `results/manifest.json`: file SHA256, rows, columns, digest total, digest version 1 | same keys, same digest definition |
| Generate the SQL | `simd_ingest/sql_check.py` writes `import_csv.sql` and `check_loaded_digest.sql` | the same generator, extended with the two types |
| Load | `local/load_simd_to_sqlserver.py`: verify hashes, BULK INSERT into staging, cast, run the check | copy with the AHAH table name and expected values filled in |

The postcode-simd modules are copied, not reused as they are. Their types are string, date,
bool, int8, int16 and a one-decimal rank, and the text renderer passes any other number through
`int()`, which would turn 2.36 into 2. AHAH needs two more types, with one rendering in Python
and in SQL and a round-trip test for each:

- `decimal`: SQL `decimal(38,20)`, parsed from the file text with Python's `Decimal`, never
  through a float. The files carry up to 20 fractional digits (12,106 Scottish cells of v5.1
  and 2,621 of v3 have more than 16), and v3 writes some values in scientific notation such as
  `6.225548837442603e-05`. The canonical rendering, in the CSV and in the digest on both sides,
  is fixed notation with 20 decimals. The build fails on a value that does not fit.
- `int32`: SQL `int`, for ranks up to 43,064.

The digest definition stays at version 1: the two new renderings are new column kinds, not a
change to how a row is framed and hashed.

## The editions

GeoDS lists six releases. The HEAL-Scot documents name only version 4 and version 5.1, but the
table accepts any of them.

| Version | Date | Scottish geography |
| --- | --- | --- |
| 1 | 2016 | 2011 data zones, the original method |
| 2 | 2017 | 2011 data zones, revised method, used by every later version |
| 3 | late 2022 | 2011 data zones |
| 4 | late 2024 | 2011 data zones |
| 5 | February 2026 | 2022 data zones, the first release on them |
| 5.1 | May 2026 | 2022 data zones, refines the definition of a hospital |

Versions 1 to 4 are in a separate GeoDS record, "Previous versions", downloaded on 29 October
2026 and listed in `data/sources/geods_previous/SOURCES.md`. No edition is comparable with
another; see the warning under "The table". Column names differ in every edition (`lsoa11`,
`ah4gp`, `GP` and so on), so the build keeps a per-edition mapping file to the table's names,
recorded in the decision log.

## The table

One table, `ahah_datazone`, one row per Scottish data zone per edition, keyed by
`ahah_version` and `datazone_code`. The column names are those of the version 5.1 file where
it has the column, so a reader finds them in its dictionary and report. Earlier editions map
onto them where the concept is the same. Some groups of columns exist only for the older
editions: the off-licence indicator and its decile, the `ur` flag, the decile columns, and the
four exponential-scale domain columns.
A column an edition does not publish is NULL for it. Within an edition no measured value is
missing: every data summary shows zero nulls.

Which edition publishes what. "y" means present, "-" means NULL in the table.

| Column group | v1 | v2 | v3 | v4 | v5.1 |
| --- | --- | --- | --- | --- | --- |
| `datazone_code` (file column `lsoa11`, `lsoa11`, `lsoa11`, `LSOA21CD`, `lsoa21cd`) | y | y | y | y | y |
| 12 indicators common to all: `GP`, `hospital`, `dentist`, `pharmacy`, `leisure`, `gambling`, `fast_food`, `pub_bar`, `tobacco`, `NO2`, `PM10`, `SO2` | y | y | y | y | y |
| `greenspace` (passive) | y | y | y | y | y |
| `bluespace` | - | y | y | y | y |
| `greenspace_active` | - | y | - | - | y |
| `off_licence` (file `off`), older editions only | y | y | - | - | - |
| `ur`, version 2 only, a 0/1 flag, probably urban = 1, not documented (see the v1 to v4 `SOURCES.md`) | - | y | - | - | - |
| indicator `_rnk` | - | - | y | y | y |
| indicator `_pct` | - | - | y | y | y |
| indicator `_dec` | y | y | - | - | - |
| domain scores `domain_h`, `domain_e`, `domain_r`, `domain_g`, probit scale | - | - | y | y | y |
| `domain_h_exp`, `domain_e_exp`, `domain_r_exp`, exponential scale | y | y | - | - | - |
| `domain_g_exp`, exponential scale | - | y | - | - | - |
| domain `_rnk` | - | y | y | y | y |
| domain `_pct` | - | - | y | y | y |
| domain `_dec` | y | y | - | - | - |
| `ahah`, `ahah_rnk`, `ahah_pct`, `ahah_dec` | score, decile | score, rank, decile | score, rank, pct | score, rank, pct | score, rank, pct |

So v3 and v4 have 14 indicators, v5.1 has 15, v1 and v2 have 14 and 16 with the off-licence
column. The per-edition mapping file lists every column of every file exactly once, each to a table
column. Nothing is dropped: every published value is kept. The build fails on a file column not
in the mapping or a mapped column not in the file.

Versions 1 and 2 publish no domain score of the kind v3 onward publish. Their domain columns
are the exponentially transformed domain ranks, on a 0 to 100 scale where 100 is the worst rank:
the v1 build code (`create_index_v1.R`, lines 88 to 123, commit `27b2067`) ranks each domain
score and applies the exponential transformation, and the v2 code applies `exp_trans` to each
domain rank. They are what each edition's index averages. The check: with n = 41,729, every
published v1 `h`, `e` and `r` value inverts through `n·(1−exp(−x/23))/(1−exp(−100/23))` to
within 0.000006 of an integer rank (probed 29 October 2026, round 3). So v1 `h`, `e` and `r` go
into `domain_h_exp`, `domain_e_exp` and `domain_r_exp`, and v2 `h_exp`, `g_exp`, `e_exp` and
`r_exp` into the same columns plus `domain_g_exp`. These columns are NULL for v3 onward, and
`domain_g_exp` is NULL for v1, which has no green domain. The probit-scale columns
`domain_h` and friends are NULL for v1 and v2. The dictionary says the two sets are on
different scales. A fidelity check compares the three v1 and four v2 values of every zone with
the file. The inverted ranks are evidence about the scale only; the build does not derive or
publish them. The v1 environment domain includes green space as well as the air pollutants
(same source), and the per-edition dictionary says so.

Types:

| Column | SQL type | Notes |
| --- | --- | --- |
| `ahah_version` | nvarchar(8) | `1`, `2`, `3`, `4`, `5.1` |
| `datazone_vintage` | smallint | 2011 for v1 to v4, 2022 for v5.1 |
| `datazone_code` | nvarchar(9) | `S01` codes only |
| scores and indicators | decimal(38,20) | see the type note above |
| `_rnk` | int | rank over Great Britain, 1 is the healthiest. The ranked population is 41,729 (v1 to v3), 42,648 (v4) or 43,064 (v5.1), so a rank is read with its edition. v4 ranks the five health indicators densely, so its largest health rank is below the population |
| `_pct` | tinyint | indicators 0 to 100, domains and index 1 to 100 (`PERCENTILES.md`) |
| `_dec` | smallint | 1 to 10, and `-1` in version 2 (below) |
| `ur` | tinyint, NULL outside v2 | 0 or 1 as published. Not `bit`: the copied writers' boolean path (`text_output.py` `bool(v)`, `output.py` `astype(bool)`) turns a null into 0 or 1, while the nullable-integer path keeps it NULL. A check restricts v2 values to 0 and 1 and requires NULL elsewhere |

Units and definitions differ by edition and are recorded per edition in the data dictionary,
not once for the table:

- v1: accessibility is network distance in kilometres, and passive green space is an area
  measure of green space within a 900-metre buffer, not NDVI (Daras et al. 2019, pages 1 and
  4). The unit of that area is not stated in the paper and stays unconfirmed; the Scottish
  values run from 0 to 277.5, so it is not a share, and the dictionary gives it no range rule.
- v2: the published documentation is not held; the column names (`gact`, `gpas`, `blue`)
  suggest the v2 method, but units are unconfirmed.
- v3, v4, v5.1: drive time in minutes, median NDVI for passive green space, annual mean µg/m³
  for air (v5 methodology report, sections 3 and 5).

So the Scottish median GP values quoted for the five editions (1.32, 1.34, 3.93, 2.64, 2.36)
are not all minutes, and the README says so where it warns against comparing editions.

Version 2 publishes `-1` in two Scottish zones, `S01010206` and `S01010226`, in eleven raw
indicators and their eleven deciles. The table keeps the value as published, the data dictionary
describes `-1` as the edition's code for "no route" (the two zones are Glasgow regeneration
areas with no population; see the v1 to v4 `SOURCES.md`; no v2 documentation states it), and the check for the code is narrow: it applies to the v2 decile
columns, whose valid values are 1 to 10, and to the eleven v2 indicator columns, where a
distance cannot be negative. A domain score is a real number and can legitimately be `-1`: v4
zone `S01008132` has an air quality domain score of exactly `-1.0000`, with rank 5,702 and
percentile 14, and it loads as an ordinary value. Nobody should average a v2 indicator
without excluding the code.

Ranks and percentiles are over Great Britain. A Scotland-only rank would be a computed column
with its own name and a decision log entry, and is not planned.

Indicator percentiles run 0 to 100 and domain and index percentiles 1 to 100, because the
published build code uses two formulas (`docs/PERCENTILES.md`). An issue was logged with the
authors on 29 October 2026. Until they answer, the values are stored as published and the
checks use those ranges. If a corrected file is released, it is a new pinned source and a new
build, never an edit of this one.

The reference lists of data zones, against which the build checks that every zone of a
vintage is present once, are pinned as sources of their own, independent of any postcode
product: the Scottish Government's 2011 data zone boundaries or lookup (6,976 zones) and the
2022 data zone boundaries or lookup (7,392 zones). postcode-simd pins the 2011 list inside its
SIMD shapefiles and no 2022 list; both are added here explicitly, and the registry names the
publisher page and hash of each.

## Files the build produces

- `results/ahah_datazone.csv.gz`, the shared form, and `results/ahah_datazone.parquet`.
- `results/manifest.json`: SHA256 and byte count of both, row count, column count, digest total
  and digest version, plus the SHA256 of each pinned source file and the version chosen.
- `results/BUILD_REPORT.md`: every check with its result, the row count per version, and three
  data zones shown cell for cell against the source CSV.
- `docs/sql/import_csv.sql` and `docs/sql/check_loaded_digest.sql`, generated.
- `docs/DATA_DICTIONARY.md`, generated from the schema file, one row per column with the
  dictionary text AHAH publishes for it.

## Loading into SQL Server

1. Carry four files: the CSV, the two SQL scripts and `load_ahah_to_sqlserver.py`.
2. Fill in server, database and the CSV folder. The script uses Windows authentication unless
   given a connection string, and stores no password.
3. The script checks the CSV's SHA256 against the manifest before it connects.
4. `import_csv.sql` drops and recreates `staging_ahah_datazone` as text with the binary UTF-8
   collation, bulk inserts, then creates `ahah_datazone` with the declared types and the primary
   key on (`ahah_version`, `datazone_code`).
5. `check_loaded_digest.sql` confirms the columns, types, nullability and order, the key, the
   absence of the framing characters, the row count and the digest. The expected numbers are
   pasted from the manifest, never read from the loaded table.
6. The loader prints the check table. Any failed row stops the release.

## Joining by data zone

HEAL-Scot releases no postcode and no data zone. Each site maps its patients to a data zone and
replaces the code with a pseudonymised data-zone ID. AHAH is therefore joined by data zone alone,
and this build does not need the postcode-simd tables. The join is a left join, so no cohort
row disappears, and every row gets a status, as the main plan's section 6 requires:

```sql
-- AHAH 5.1 for a cohort table that carries the patient's 2022 data zone.
SELECT c.pseudo_id, a.ahah, a.ahah_rnk, a.ahah_pct,
       CASE WHEN c.DataZone2022Code IS NULL OR LTRIM(RTRIM(c.DataZone2022Code)) = N'' THEN N'no_code'
            WHEN a.datazone_code IS NOT NULL                                              THEN N'matched'
            WHEN v.datazone_code IS NOT NULL                                              THEN N'other_vintage'
            ELSE                                                                               N'not_a_datazone' END AS ahah_status
FROM cohort AS c
LEFT JOIN ahah_datazone AS a
       ON a.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2022Code))) AND a.ahah_version = N'5.1'
LEFT JOIN ahah_datazone AS v
       ON v.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2022Code))) AND v.ahah_version = N'4';
```

The HEAL-Scot release uses version 4 on the 2011 data zones, which is the vintage the
project's pseudonymised mapping already covers. The same query, with the twelve columns the
project asked for:

```sql
-- AHAH 4 for a cohort table that carries the patient's 2011 data zone.
SELECT c.pseudo_id,
       a.dentist, a.GP, a.hospital, a.pharmacy,
       a.domain_h, a.domain_g, a.domain_e, a.domain_r,
       a.ahah, a.ahah_rnk, a.ahah_pct,
       CASE WHEN c.DataZone2011Code IS NULL OR LTRIM(RTRIM(c.DataZone2011Code)) = N'' THEN N'no_code'
            WHEN a.datazone_code IS NOT NULL                                              THEN N'matched'
            WHEN v.datazone_code IS NOT NULL                                              THEN N'other_vintage'
            ELSE                                                                               N'not_a_datazone' END AS ahah_status
FROM cohort AS c
LEFT JOIN ahah_datazone AS a
       ON a.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND a.ahah_version = N'4'
LEFT JOIN ahah_datazone AS v
       ON v.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND v.ahah_version = N'5.1';
```

These twelve are raw scores and a rank, and the rank alone identifies the zone, so this is the
analyst's query inside the safe haven, not the release shape (see the disclosure section of the
main plan).

The clean-up is trim and upper case only, as in the SIMD data zone procedure. A code of the
other vintage is reported, never converted. A test runs the query over a cohort with every
status and asserts that every input row comes back once.

The one thing the join needs from the site is a data zone of the right vintage. The HEAL-Scot
data request maps 2011 data zones to pseudo IDs, which reaches version 4 only. Version 5.1 needs
a second mapping on 2022 data zones. The DataLoch data selection form already says version 5.1
on 2022 zones, and which AHAH variables to carry is "HEAL-Scot data team to decide".

A build test joins every data zone of the pinned reference list of the vintage and reports any
zone without an AHAH row. The postcode route stays possible for other projects through the
postcode-simd history table, which carries both data zone codes on every postcode life, but it
is not part of this plan.

## Tests

- The export refuses a text value containing NCHAR(0) or NCHAR(31), as postcode-simd does.
- The manifest digest of a synthetic ten-row table equals the digest the check script computes
  on SQL Server for the same rows. This is the one test that needs a SQL Server, and it runs
  only when a connection string is in the environment.
- A changed cell in the loaded table fails the digest check.
- Every decimal value of every edition round-trips: file text, `Decimal`, canonical rendering,
  back to `Decimal`, equal to the parsed value. Scientific notation included. A value that does
  not fit decimal(38,20) fails the build.
- The SQL rendering of a decimal(38,20) and an int equals the Python rendering for a table of
  chosen values (negative, scientific notation, 20 decimals, the v2 `-1`).
- The two v2 zones with `-1` load and pass the checks. The v4 zone `S01008132` with an air
  domain score of `-1.0000` loads as a value and passes. A `-1` in a v2 decile or indicator
  column of any other zone, or in any decile or distance column of another edition, fails.
- Every v2 zone's four `_exp` values and every v1 zone's three equal the file; `domain_g_exp` is NULL for v1 and all `_exp` columns are NULL for v3 onward.
- `ur` round-trips the values NULL, 0 and 1 through CSV, Parquet, digest and SQL with NULL kept as NULL; a 2 or a NULL in a v2 row fails.
- The row count of each file before the Scottish filter equals its data summary (41,729,
  41,729, 41,729, 42,648, 43,064).
- The left join returns every cohort row once, with the right status for a matched code, an
  empty code, a code of the other vintage, a malformed code, and a lower-case code with spaces.
- Each edition's mapping file names every published column exactly once; an unmapped or
  unknown column fails the build.
- Every data zone of the pinned reference list of the vintage finds exactly one AHAH row.

## Order of work

1. Settled on 29 October 2026: HEAL-Scot releases version 4 on the 2011 data zones. The build carries all five regardless.
2. Done: files of every edition downloaded and hashed, column table written from the files.
3. Done on 29 October 2026 (`ahah_ingest/`, 31 tests, SQL Server probe in `docs/sql/SQLSERVER_PROBE_2026-10-29.md`). Create `ahah_ingest` from the postcode-simd layout: registry, reader, checks, schema,
   contract, text output, manifest, SQL generator. The reader, the checks and the per-edition
   mapping are new. The text output, the Parquet writer and the SQL generator are copied and
   extended with the `decimal` and `int32` types described above. Two or three sessions.
4. Done on 29 October 2026. Generate the SQL, write the loader, run the SQL Server test once against a test database.
5. README, data dictionary, example joins and decision log done on 29 October 2026. Zenodo record: pending.

## Open questions, beyond those in AHAH_Plan.md

- Whether to publish the Great Britain ranks only, or also a computed Scotland rank.
- Whether the loader lives in this repository or beside the SIMD loader in `SIMD/local`, so one
  script loads both tables.
