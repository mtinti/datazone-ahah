# AHAH notebook upload review

Date: 29 October 2026. Reviewer: Codex.

Scope: the update after [implementation review round 2](AHAH_implementation_review_2026-10-29_round2.md),
particularly `loader/upload_ahah.ipynb`, its generator, the new source-comparison
command, the moved loader, and the asserted join in the shell probe. Implementation
files and supplied outputs were not changed. Tests used temporary delivery folders,
an isolated database and a disposable SQL Server container.

The notebook successfully uploads the supplied data through a real Jupyter kernel.
Its loaded values, NULLs, digest and example join pass. Two findings remain:
one P1 affecting replacement of an existing table, and one P2 in the additional
comparison tool.

1. **P1 — Make the setup checks block execution before dropping the destination table.**
   Location: [loader/make_notebook.py](../../loader/make_notebook.py), lines 82–91
   and 180–183; generated notebook Step 1 (code cell 2) and Step 3 (code cell 6).

   Step 1 prints missing files and displays `can_create_table`, but never raises
   when either check fails. Its accompanying text says missing files or rights
   fail before anything is dropped. Step 3 then drops the existing table with
   `autocommit=True` before attempting `CREATE TABLE`.

   Reproduced with a test login granted `ALTER`, `SELECT` and `INSERT` on the
   destination schema, but without database-level `CREATE TABLE` permission. An
   existing destination table contained a marker row. Step 1 displayed
   `can_create_table = 0` and returned normally; Step 2 accepted the correct CSV;
   Step 3 dropped the existing table and then failed with SQL Server error 262,
   `CREATE TABLE permission denied`. An independent query confirmed that the
   original table no longer existed.

   A second reproduction omitted `check_loaded_digest.sql` from the delivery
   folder. Step 1 printed `MISSING` and continued. Steps 2–4 replaced the previous
   destination and loaded all 35,296 rows. Only Step 5 failed, with
   `FileNotFoundError`, after replacement had already happened.

   Validate all required files and the necessary permissions before any DDL,
   raising a clear exception when a prerequisite fails. Protect DROP/CREATE with
   a transaction so that a failed CREATE preserves the previous table. Add
   regressions asserting that a marker table survives both missing-file and
   insufficient-permission cases.

2. **P2 — Reject duplicate keys before constructing the comparison lookup.**
   Location: [loader/compare_sql_with_sources.py](../../loader/compare_sql_with_sources.py),
   lines 28–32.

   The command stores fetched rows in a dictionary keyed by edition and data zone.
   A repeated key silently overwrites the earlier row. It then reports the
   dictionary size as the number of rows read, so the duplicate is invisible to
   both the reported row count and the value comparisons.

   Reproduction against the correctly uploaded table:

   ```sql
   SELECT * INTO dbo.ahah_duplicate_probe FROM dbo.ahah_datazone;
   INSERT INTO dbo.ahah_duplicate_probe
   SELECT * FROM dbo.ahah_datazone
   WHERE ahah_version = '4' AND datazone_code = 'S01006506';
   ```

   The copy contains **35,297 physical rows**. Running the comparison command on
   it printed **35,296 rows read**, **0 differences**, and exited **0**. Identical
   duplicates therefore receive a false success. A duplicate with different
   values can also be hidden when the correct row happens to overwrite it.

   Count physical rows and fail on repeated keys before inserting into `loaded`.
   Add a duplicate-row regression, including an identical duplicate. The
   notebook's own key/count/digest checks remain effective; this defect concerns
   the separate command advertised as an independent source comparison.

Verification completed:

| Check | Result |
| --- | --- |
| Existing Python suite | **37 passed**, using `python -m pytest -q -p no:cacheprovider`. |
| Notebook structure | Valid nbformat 4.5; 15 cells, seven code cells; every code cell parses. No saved execution outputs in the supplied notebook. |
| Generator consistency | Regenerated cell types, cell sources and kernel metadata in memory; all match the supplied notebook. |
| Actual Jupyter execution | All seven code cells executed successfully in a native macOS kernel through `nbclient`, with execution counts 1–7 and no error outputs. This was a kernel run, beyond the earlier script-only probe. |
| Client-side upload | 35,296 rows uploaded through pyodbc in about three seconds. The CSV remained on the client; no server-side CSV or BULK INSERT was used. |
| SQL structure and digest | 90 columns, 87 nullable columns, the two-column primary key, and all five checks passed. Digest: `1313739416145945439820`. |
| Edition NULL counts | `ur`: 28,320; `domain_h_exp`: 21,344; `greenspace_active`: 20,928, all as expected. |
| Published values | The new comparison command checked **1,860,064 published cells** and **1,245,984 absent-edition cells**, with **zero differences** on the valid upload. |
| Changed SQL values | Changing v4 `S01006506.GP` from `2.32090000000000000000` to `2.32090000000000000001`, and v3 `S01006506.ur` from NULL to 1, made notebook Step 5 fail. The comparison command reported exactly those two differences and exited 1. Restoring the values restored the digest pass. |
| Corrupt CSV | Changing one decimal cell while retaining the row and column counts made Step 2 reject the file by SHA256. |
| Example join | All eight cohort rows returned once with the expected statuses; the notebook's assertions passed. |
| Missing validation file | Reproduced the late failure after replacement and loading, as described in finding 1. |
| Missing CREATE permission | Reproduced loss of the previous destination before CREATE failed, as described in finding 1. |
| Duplicate SQL row | Reproduced the false-success comparison, as described in finding 2. |

The kernel test used Python 3.12.12, pandas 3.0.3, pyodbc 5.3.0, nbclient 0.10.2,
ipykernel 7.0.1 and Microsoft ODBC Driver 18. The server was SQL Server 2022 Developer,
`16.0.4305.5`, on Linux. Only the notebook's connection and delivery-folder settings
were changed in the temporary test copy; SQL authentication replaced Windows
integrated authentication. The failure probes executed the relevant notebook cell
sources against separate test tables. Windows integrated authentication remains
untested. The test environment supplied the notebook and ODBC dependencies; a clean
installation from `requirements.txt` alone was not tested.

The original ingestion code, source registry, mapping, schema and output writers
are unchanged since round 2. The relocated command-line loader is byte-identical
to the version previously tested. The shell probe now compares its eight-row join
output with an expected list and exits on a difference, addressing the previous
observation; that shell script was inspected, while this round exercised the
notebook's upload and join. CSV and Parquet hashes are unchanged, so a rebuild of
the unchanged ingestion pipeline was not repeated.

The 37 existing tests do not execute the notebook or the new comparison command.
The live integration and failure probes above supplied that coverage for this
review; the two reported cases should become repeatable regression tests.

SHA256 values identify the reviewed versions:

| File | SHA256 |
| --- | --- |
| `loader/make_notebook.py` | `60053f74be4b8c94a827f8c7dffa412916983b523b3811eb68c9c929f8c9b204` |
| `loader/upload_ahah.ipynb` | `05692b46961efe732066160c2eb2dc0ecf5ef14e9251c453b67e5d67a43c4109` |
| `loader/compare_sql_with_sources.py` | `f8bbb2829018e2df958240e21df5ac50e07b44fb6be273b4c42ca0ceea9ac876` |
| `loader/load_ahah_to_sqlserver.py` | `3c97cf30ff7b3a968ba4f45a56ca9642085d4d07068f4f048a2e3f7291e07098` |
| `loader/sqlserver_probe.sh` | `24570896e05775785403516c6b7d55d78f3a4c3586c275dfd987c2c45effe73c` |
| `results/ahah_datazone.csv.gz` | `505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574` |
| `results/ahah_datazone.parquet` | `6fef707bd50a5aefeb6c376295cb56e9c699d5b140c06c175261ea3c6221ee54` |
