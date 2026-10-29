# SQL Server probe, 29 October 2026

Run with `sh loader/sqlserver_probe.sh` against a throwaway SQL Server 2022 container
(`mcr.microsoft.com/mssql/server:2022-latest`, linux/amd64 under emulation, Developer edition),
on the build whose CSV SHA256 is `505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574`.

## Import and check

`docs/sql/import_csv.sql` bulk inserted 35,296 rows; `docs/sql/check_loaded_digest.sql` with the
manifest's numbers:

| Check | Expected | Actual | Outcome |
| --- | --- | --- | --- |
| columns declared and in order | 0 differences | 0 differences | pass |
| natural key unique and not null | 0 offending rows | 0 offending rows | pass |
| no reserved framing characters in text | 0 rows | 0 rows | pass |
| row count | 35296 | 35296 | pass |
| row digest, definition version 1 | 1313739416145945439820 | 1313739416145945439820 | pass |

## Rendering

For five zones (v1 S01006506, v2 S01010206, v3 S01006506, v4 S01008132, v5.1 S01013482) and eight
columns (`GP`, `domain_e`, `ahah`, `ahah_rnk`, `GP_dec`, `ur`, `domain_h_exp`, `SO2`), SQL Server's
`CONVERT(varchar(40), decimal(38,20))` and `CONVERT(varchar(11), int)` text equals the CSV text for
all 40 cells, NULLs included. The cells cover a negative score, the v2 `-1` code, the v4 domain
score of exactly `-1.0000`, and values with 16 or more fractional digits.

## Join

A seven-row cohort with a matched code, NULL, empty, a 2022 code, a malformed code, a lower-case
code with spaces, and a repeated code returned seven rows with statuses `matched`, `no_code`,
`no_code`, `other_vintage`, `not_a_datazone`, `matched`, `matched`.

## Tampering

Adding `0.00000000000000000001` to one v4 `GP` and setting one v2 `ur` to NULL changed the digest
to `1318347800640415772910` and the check script threw. Restoring both cells restored the pass.

## Not covered

- Only SQL Server 2022 on Linux. The collation `Latin1_General_100_BIN2_UTF8` needs 2019 or later.
- `BULK INSERT` from a Windows path and Windows authentication were not exercised here; the loader
  rewrites the path and uses them as postcode-simd's does.

## Second run, after the implementation review

Same container image, after the fixes recorded in
`../reviews/AHAH_implementation_review_2026-10-29_response.md`:

- Default name: the five checks pass again with the same digest total; rendering and join
  probes unchanged.
- Shadow schema: with an empty `shadow.ahah_datazone` present and `dbo.ahah_datazone.GP`
  altered to NOT NULL, the regenerated check reports **1 difference** in "columns declared and
  in order" and throws. Restoring nullability and dropping the shadow table restores the pass.
- Loader with `MAIN_TABLE = "dbo.ahah_datazone"`: `--print-sql` wrote both filled scripts; both
  executed; all five checks pass under the qualified name.

## Third run: the upload notebook

`loader/upload_ahah.ipynb`, the pyodbc path for a client that the server cannot read files from,
executed cell by cell inside the same container (as a script, with `display` printing; the
Jupyter kernel does not start under emulation). SQL authentication in place of Windows
authentication; nothing else changed. Steps 1 to 7 all passed: hash match, 90-column table with
the two-column key, 35,296 rows loaded in 3 seconds, five checks pass with the digest total
`1313739416145945439820`, the rows per edition as expected, the twelve HEAL-Scot columns shown,
and the eight-row join asserted.

## Fourth run: the loaded table against the original GeoDS files

`loader/compare_sql_with_sources.py` reads the five source CSVs with the csv module and
Decimal, maps columns with `mapping.yaml`, pulls the whole table through pyodbc and compares
value by value, independent of the build's reader and writers. On the table loaded by the
notebook: 35,296 rows, **1,860,064 published cells equal, 1,245,984 absent-edition cells NULL,
0 differences**. Then two cells were changed (one v4 `GP` by 1e-20, one v3 `ur` from NULL to 1):
the script reported exactly those two and exited 1. Restored by reloading.
