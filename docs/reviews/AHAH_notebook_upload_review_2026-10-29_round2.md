# AHAH notebook upload review, round 2

Date: 29 October 2026. Reviewer: Codex.

Scope: changes since the [notebook upload review](AHAH_notebook_upload_review_2026-10-29.md),
checked against its [response](AHAH_notebook_upload_review_2026-10-29_response.md).
Reviewed the updated notebook and generator, comparison command, new tests and
SQL probe record. No implementation files or supplied outputs were edited.

**Both original findings are resolved, including the P1 table-loss issue.**
The notebook passed a real Jupyter kernel run and the live regression cases on
SQL Server. One new P2 finding concerns running the new tests without local
build artifacts.

1. **P2 — Make the new guard tests independent of ignored build outputs, or skip them explicitly.**
   Location: [tests/test_notebook_and_compare.py](../../tests/test_notebook_and_compare.py),
   lines 95–102, particularly the unconditional `gzip.open` at line 98.

   The `delivery` fixture always reads `results/ahah_datazone.csv.gz`. That file is
   excluded by `.gitignore` and is not present in a source-only checkout. All four
   guard/transaction tests use this fixture without an availability condition, so
   they fail during setup before exercising any notebook logic.

   Reproduced in a temporary copy containing the current code, tests, notebook,
   YAML definitions and generated SQL, with downloaded source data and build
   outputs omitted. Running `python -m pytest -q -p no:cacheprovider` produced
   **32 passed, 6 skipped, 4 errors**. All four errors were `FileNotFoundError`
   for `results/ahah_datazone.csv.gz`, in:

   - `test_missing_file_stops_step_1_before_any_sql_that_drops`
   - `test_missing_create_right_stops_step_1`
   - `test_failed_create_rolls_the_drop_back`
   - `test_successful_create_commits_once`

   With the developer's local artifacts present, all **42 tests pass**. That
   success therefore does not establish that the source-only test suite works.

   Prefer small, self-contained fixtures for these guard and transaction tests;
   their behavior does not require the full published dataset. Alternatively,
   explicitly skip tests that require a build when their inputs are absent.
   Artifact-dependent availability checks should cover every input used, including
   the Parquet read by the comparison test. Keep the live-data checks separate
   from the tests that can run from the committed source alone.

| Previous finding | Resolution and independent verification |
| --- | --- |
| P1: setup warnings allow a destructive DROP before failure | Step 1 now raises for a missing file or missing CREATE TABLE permission. Both live reproductions stopped at Step 1 and preserved their marker rows. Step 3 uses one transaction, rolls back on CREATE failure, and commits only after both DDL statements succeed. Calling Step 3 directly as the restricted login produced SQL Server error 262 and preserved the original marker row `42`, even with the Step 1 guard bypassed. |
| P2: identical duplicate rows receive a false-success comparison | The command now counts physical rows and records repeated keys before inserting into its lookup. The valid table returned 35,296 physical rows, 35,296 distinct keys, zero differences and exit 0. A copy with one identical duplicate returned 35,297 physical rows, 35,296 distinct keys, one repeated-key difference and exit 1. |

Verification completed:

- Ran the complete local Python suite: **42 passed**. Ran the same tests in the
  temporary source-only copy: **32 passed, 6 skipped, 4 setup errors**, as above.
- Validated the notebook format and parsed all seven code cells. Regenerated
  cells in memory and confirmed that their types and sources match the supplied
  notebook.
- Executed all seven notebook code cells through a native Jupyter kernel, with
  execution counts 1–7 and no error outputs. Only delivery-folder and test-server
  connection settings changed in the temporary copy.
- Uploaded **35,296 rows** through pyodbc, with 90 columns and the two-column key.
  All five SQL checks passed, including digest `1313739416145945439820`; the
  eight-row join assertions also passed.
- Ran the updated comparison CLI against that actual upload: **1,860,064 published
  cells** and **1,245,984 absent-edition cells** checked, with **zero differences**.
- Exercised the missing-check-file guard, missing-CREATE-permission guard,
  transactional rollback after a denied CREATE, and identical-duplicate rejection
  against the isolated SQL Server database. All four live regressions passed.
- Confirmed that the existing ingestion code and output files are unchanged.
  Earlier ingestion and numeric-fidelity evidence remains applicable; the build
  was not rerun for these notebook/test changes.

The kernel used Python 3.12.12, pandas 3.0.3, pyodbc 5.3.0, nbclient 0.10.2,
ipykernel 7.0.1 and ODBC Driver 18. The disposable server was SQL Server 2022
Developer on Linux, using SQL authentication. Windows integrated authentication
remains untested. The restricted test login had ALTER, SELECT and INSERT on `dbo`,
but no database CREATE TABLE permission, matching the previous failure scenario.

SHA256 values identify the principal changed files reviewed:

| File | SHA256 |
| --- | --- |
| `loader/make_notebook.py` | `6beda89096f43ffdbaf4a6ee9c8facfd75110fa93f059e8912a8be9966dfbd4b` |
| `loader/upload_ahah.ipynb` | `176daf739788ad1af4b3d9bb7fe449466399a5088ade4167f74b7e397d49ae4b` |
| `loader/compare_sql_with_sources.py` | `3b61cdd1daa0113365d4e6ced83cc640b253bcb851615d206efaf8dd0b64b477` |
| `tests/test_notebook_and_compare.py` | `f2e581ad7c1c2a3e61c26acd102f6b7bb0d419dabfd049a3d7868d02ae74da5c` |
| `docs/sql/SQLSERVER_PROBE_2026-10-29.md` | `cb7085882344f6e60790b7381ab3cc6abe2d40fd503b81b717e4c4195f77f556` |
