# Response to the implementation review (29 October 2026)

Every finding was reproduced before it was fixed, and each fix was probed again on SQL Server
2022 (`../sql/SQLSERVER_PROBE_2026-10-29.md`, second run).

1. **Loader crash (P1): fixed.** `rename_tables("ahah_datazone")` raised the reported
   `ValueError`; the loop now iterates a one-element sequence of pairs. New `tests/test_loader.py`
   loads the real loader file and calls `rename_tables`, `filled_import` and `filled_check` for
   the default name, `dbo.ahah_datazone` and `geo.ahah_v1`. On SQL Server, the loader's own
   filled scripts for `dbo.ahah_datazone` imported and passed all five checks.
   Not covered: a real connection through pyodbc or sqlcmd from the loader, and Windows paths.

2. **Schema-qualified name in a variable (P2): fixed in the generator.** The table variable is
   now the fixed `@declared`, so no table name is ever substituted into it. The loader test
   asserts `@declared_` and `@declared.` never appear in a filled script.

3. **Structure check bound by name only (P2): fixed.** Both metadata queries now read
   `sys.columns` joined to `sys.types`, filtered by `OBJECT_ID(N'<table>', N'U')`. The review's
   reproduction (empty `shadow.ahah_datazone`, `dbo.ahah_datazone.GP` altered to NOT NULL) now
   fails the check with one difference; restoring it passes.
   Not covered: a table whose columns were added and dropped so that `column_id` is not
   contiguous; the check compares `column_id` with the declared ordinal and would report a
   difference on such a table, which is the safe direction.

4. **Version 2 code in non-routed deciles (P2): fixed.** The `-1` exception now applies only to
   the deciles of routed indicators (the eleven, including blue space), and a new check,
   `v2.no_route_code_outside_routed`, fails on `-1` in any other v2 decile or indicator, the
   two no-route zones included. The test sets each of the five non-routed deciles and two raw
   indicators to `-1` in an ordinary zone and in a no-route zone and asserts both the range
   check and the location check fail; the published frame still passes.

5. **Index definition (P2): fixed.** The description of `ahah` now says the index is the mean of
   the exponentially transformed domain ranks, three domains in v1 and four from v2, and that the
   probit domain scores of v3 onward are intermediates on another scale which the index does
   not average, citing the v4 code lines. Schema and dictionary regenerated. The schema file's hash
   changed in the manifest; the Parquet metadata does not carry it, so neither output file's hash
   changed, and the CSV digest is the same.

Rebuilt after the fixes: 35,296 rows, 341 checks passed (one more than before, the new v2
check), CSV SHA256 unchanged, 37 tests passing.

My findings on this review are closed.
