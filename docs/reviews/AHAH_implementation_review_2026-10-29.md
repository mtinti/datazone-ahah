# AHAH implementation review

Date: 29 October 2026. Reviewer: Codex.

Scope: `ahah_ingest/`, the generated schema and mapping, the loader and SQL scripts,
tests, generated outputs, README and data dictionary, against the reviewed plans.
Source registries, publisher code and pinned data were used as evidence. The
implementation and supplied outputs were not edited; rebuilds and mutation probes
used a temporary directory and a separate SQL Server container.

The data build is faithful to the pinned sources, but the implementation is not ready
for the documented loading workflow. There is one P1 finding and four P2 findings.
All five are reproducible; the passing Python suite does not cover the loader failure.

1. **P1 — The loader crashes while filling either SQL script, including with its default table name.**
   Location: [local/load_ahah_to_sqlserver.py](../../local/load_ahah_to_sqlserver.py),
   line 141.

   `for key, chosen in (("main", MAIN_TABLE)):` iterates the two strings, rather than
   a sequence containing one pair. Its first iteration tries to unpack `"main"` and
   raises `ValueError: too many values to unpack (expected 2)`. A direct call to
   `rename_tables("ahah_datazone")` reproduces this without a database. Both
   `filled_import()` and `filled_check()` call it, so an otherwise configured normal
   load, `--check-only`, and `--print-sql` all fail before executing their SQL.

   Make this a one-element sequence of pairs, or remove the redundant loop. Add
   tests exercising the actual loader's SQL filling functions. The existing
   `local/sqlserver_probe.sh` substitutes names and expectations with `sed` and
   never imports the loader, which explains why that probe can pass despite this bug.

2. **P2 — Schema-qualified target names are substituted into SQL variable names.**
   Location: [local/load_ahah_to_sqlserver.py](../../local/load_ahah_to_sqlserver.py),
   lines 145–155, particularly the unrestricted replacement at line 153.

   After correcting only finding 1 in an in-memory copy, setting
   `MAIN_TABLE = "dbo.ahah_datazone"` generates
   `DECLARE @declared_dbo.ahah_datazone TABLE ...` in the check script. SQL Server
   rejects it with `Msg 102: Incorrect syntax near '.'`, followed by undeclared
   variable errors. The helper explicitly handles schema prefixes for staging
   tables and constraints, but overlooks the `@declared_ahah_datazone` variable.

   Replace table identifiers separately from local variable names, preserving a
   valid variable identifier. Test filling and executing the check for both the
   default name and a schema-qualified name. The reproduction here used a temporary
   copy solely to expose this second failure; the repository loader was not patched.

3. **P2 — The SQL structure check can validate columns belonging to a different schema.**
   Location: [ahah_ingest/sql_check.py](../../ahah_ingest/sql_check.py), lines 88–98;
   also emitted into [docs/sql/check_loaded_digest.sql](../sql/check_loaded_digest.sql).

   Both `INFORMATION_SCHEMA.COLUMNS` queries restrict `TABLE_NAME` but omit
   `TABLE_SCHEMA`. In a database with another `ahah_datazone` table, the first
   query can satisfy the expected declaration using that other table's columns.
   This defeats the independent structure check: the digest cannot detect a
   change in nullability when the stored values are unchanged.

   Reproduced on SQL Server 2022 after a successful import:

   ```sql
   CREATE SCHEMA shadow;
   GO
   SELECT TOP (0) * INTO shadow.ahah_datazone FROM dbo.ahah_datazone;
   ALTER TABLE dbo.ahah_datazone ALTER COLUMN GP decimal(38,20) NOT NULL;
   ```

   The unmodified check script, with the manifest expectations filled in, returned
   **all five checks as pass**, although `dbo.ahah_datazone.GP` was `NOT NULL`
   instead of the required nullable column. Dropping the empty shadow table made
   the same check correctly report one structural difference and throw.

   Bind both metadata queries to the actual target object, for example through
   `OBJECT_ID` and `sys.columns`, or resolve and constrain its schema explicitly.
   Include a regression case with identically named tables in two schemas.

4. **P2 — The v2 sentinel exception accepts `-1` in five columns where it is forbidden.**
   Location: [ahah_ingest/checks.py](../../ahah_ingest/checks.py), lines 60–63 and
   78–86.

   The range check removes `-1` from every v2 `indicator_dec` column, but the later
   location check examines only the eleven routed indicators and their deciles.
   Therefore `greenspace_dec`, `greenspace_active_dec`, `NO2_dec`, `PM10_dec` and
   `SO2_dec` receive neither an effective range check for `-1` nor a location check.

   Starting from the valid v2 frame, I set each of these five columns separately
   to `-1` at `S01006506`. Every call to `check_edition()` returned zero blocking
   failures. The existing test mutates only `GP_dec`, so it misses this path.
   This violates the planned restriction of the exception to the eleven routed
   columns and the two named zones. The supplied output itself has the correct
   published values; this finding concerns failure detection.

   Apply the exception only to routed deciles, and require ordinary 1–10 values
   for the other deciles. Test both an allowed routed sentinel and forbidden
   sentinels in every non-routed decile group.

5. **P2 — The generated dictionary gives the wrong definition of the later overall index.**
   Location: [ahah_ingest/columns.py](../../ahah_ingest/columns.py), line 111;
   propagated to `ahah_ingest/output_schema.yaml` lines 853–854 and
   [docs/DATA_DICTIONARY.md](../DATA_DICTIONARY.md) line 118.

   The description says the overall index averages the probit domain scores from
   edition 3 onward. The publisher's
   [v4 implementation](https://github.com/GeographicDataService/ahah/blob/722fe5f/ahah/create_index.py#L99-L104)
   instead exponentially transforms each domain rank and averages those transformed
   values. The published probit domain columns are intermediate scores on a
   different scale.

   The pinned v4 row `S01006506` makes the discrepancy concrete: its four domain
   scores average to `-0.594775`, while its published `ahah` is `9.1497`. The
   ingestion preserves those numbers correctly, but the dictionary tells a reader
   to interpret or reconstruct the index using the wrong calculation.

   Correct the authoritative description and regenerate the schema and dictionary.
   Keep the distinction between published probit domain scores and the exponential
   transformation used to construct the overall index.

Verification completed:

- Ran `python -m pytest -q -p no:cacheprovider` with Python 3.12.11 and the pinned
  pandas 3.0.3, PyArrow 24.0.0, PyYAML 6.0.3 and pytest 9.1.1: **31 passed**.
- Rebuilt all five editions into a temporary directory: **35,296 rows, 90 columns,
  340 blocking checks passed**. Both CSV gzip and Parquet hashes equal the supplied
  outputs. Source and geography pin verification passed as part of that build.
- Independently read the five source CSVs and compared their Scottish values with
  both rebuilt formats, using a separate explicit alias mapping rather than the
  implementation mapping: **1,860,064 published cells compared, zero mismatches**.
  Also checked **1,245,984 absent-edition cells** for CSV blanks and Parquet NULLs,
  with zero mismatches, plus the expected keys and edition metadata.
- Regenerated both SQL scripts and the dictionary in memory: each matches the
  supplied file. The loader's embedded file hashes and digest match this build.
- Imported the rebuilt CSV using the generated SQL in a dedicated SQL Server 2022
  Developer container, version `16.0.4305.5`, on Linux. The five default-table
  checks passed, including digest `1313739416145945439820`. SQL paths and manifest
  expectations were filled directly because the actual loader has finding 1.
- Changed only v4 `S01006506.GP` from `2.32090000000000000000` to
  `2.32090000000000000001` using an explicit decimal literal. The digest became
  `1303195265418527398705` and the check threw. Restoring the value restored all
  five passes.
- Executed the README join on ten cohort rows, with assertions for exact row
  count and statuses: matched codes, NULL, empty and whitespace-only codes, a
  2022 code, a malformed code, a nonexistent well-shaped code, lowercase/padded
  input and a repeated code all behaved as expected.
- Reproduced the loader, schema qualification, cross-schema metadata and sentinel
  failures described above. No implementation file changed during the review.

The data values, decimal precision, edition NULL matrix and default-table SQL
digest passed this review. Windows authentication and server-visible Windows file
paths were not exercised. The repository's shell probe prints join results rather
than asserting them; the review used an additional assertion-based fixture. Zenodo
publication remains explicitly pending in the plan and was not attempted.

SHA256 values identifying the principal files and artifacts reviewed:

| File | SHA256 |
| --- | --- |
| `local/load_ahah_to_sqlserver.py` | `5ef3de9bd50c145a949b0767bb8c132f3f86faac9e8e7c00556e031b23a13a43` |
| `ahah_ingest/sql_check.py` | `a24ec0387d8c99ff9d2ed3a7f0e3632272869674338c2c8be49ddec35949a50d` |
| `ahah_ingest/checks.py` | `48c41354f04c2f008bb2ff78ea3dd9e63d0ff36e843be21389d2380bd96c162b` |
| `ahah_ingest/columns.py` | `a93d39e31c0fc229d6c447808451c54c168c8d4fb4e0ba4b76a23ee9e66eaa8e` |
| `results/ahah_datazone.csv.gz` | `505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574` |
| `results/ahah_datazone.parquet` | `6fef707bd50a5aefeb6c376295cb56e9c699d5b140c06c175261ea3c6221ee54` |
