# Response to the notebook upload review (29 October 2026)

Both findings reproduced and fixed; both re-probed on SQL Server 2022
(`../sql/SQLSERVER_PROBE_2026-10-29.md`, fifth run) and covered by regression tests.

1. **Guards before the drop (P1): fixed.** Step 1 now raises `FileNotFoundError` when any of the
   three files is missing and `PermissionError` when `HAS_PERMS_BY_NAME` says the login cannot
   CREATE TABLE, so nothing later runs. Step 3 runs DROP and CREATE on one connection with
   autocommit off, commits only after both, and rolls back on any exception; SQL Server DDL is
   transactional, so the previous table survives a failed CREATE. Probed with a `limited` login:
   the marker table and its row survived error 262. Tests in `tests/test_notebook_and_compare.py`
   execute the notebook's own cell sources against a fake pyodbc: missing file and missing right
   raise before any DROP; a failing CREATE is followed by ROLLBACK and no COMMIT; a successful
   run commits once, after the CREATE.
   Not covered: a login that can CREATE but cannot DROP the existing table (DROP fails first,
   nothing changes, the error is shown); a connection lost between DROP and CREATE (the server
   rolls the open transaction back).

2. **Duplicate keys hidden (P2): fixed.** `compare_sql_with_sources.py` now counts physical rows,
   reports every repeated key as a difference before building its lookup, and prints both counts.
   The logic is a function, `compare(columns, rows, root, mapping)`, which the test drives with
   the Parquet rows: the published table gives no differences, an identical duplicate gives
   exactly one, a changed cell gives exactly one. On SQL Server, the reviewer's duplicate copy
   gives one difference and exit 1.

Tests: 42 passing. My findings on this review are closed.
