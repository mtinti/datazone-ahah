"""Generate the SQL Server scripts: import the CSV, then check the loaded table against the build.

    python -m ahah_ingest.sql_check          # rewrites docs/sql/import_csv.sql and check_loaded_digest.sql

Copied from postcode-simd's simd_ingest/sql_check.py with the types AHAH uses. The check script
confirms the declared columns, types, nullability and key, and recomputes the row digest the
build recorded, compared against the manifest, never against the loaded table. The CLI never
connects to a database.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .columns import SCHEMA
from .core.output import load_schema
from .core.text_output import DECIMAL_PRECISION, DECIMAL_SCALE, exported_columns, load_contract
from .pipeline import CONTRACT, TABLE

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
OUT = ROOT / "docs" / "sql" / "check_loaded_digest.sql"
IMPORT_OUT = ROOT / "docs" / "sql" / "import_csv.sql"
STAGING_WIDTH, TEXT_WIDTH = 100, 16

SQL_TYPE = {"string": "nvarchar", "int8": "tinyint", "int16": "smallint", "int32": "int", "decimal": "decimal"}
SQL_NUMERIC = {"decimal": (DECIMAL_PRECISION, DECIMAL_SCALE)}
SQL_DECLARED = {"decimal": f"decimal({DECIMAL_PRECISION},{DECIMAL_SCALE})", "string": f"nvarchar({TEXT_WIDTH})"}
# A decimal(38,20) renders as at most 18 integer digits, a sign, a point and 20 decimals: 40.
DECIMAL_TEXT = 40
CONCAT_CHUNK = 200
COLLATION = "Latin1_General_100_BIN2_UTF8"


def _render(name: str, kind: str) -> str:
    """One column as the text the digest hashes, never NULL: CONCAT_WS drops a NULL argument,
    which would shift every later field. CONVERT(varchar, decimal(38,20)) writes fixed notation
    with 20 decimals, a leading zero before the point and no sign on zero, as Python does."""
    if kind in ("int8", "int16", "int32"):
        return f"ISNULL(CONVERT(varchar(11), [{name}]), NCHAR(0))"
    if kind == "decimal":
        return f"ISNULL(CONVERT(varchar({DECIMAL_TEXT}), [{name}]), NCHAR(0))"
    return f"ISNULL([{name}], NCHAR(0))"


def _table_sql(table: str, name: str, schema: dict, contract: dict) -> str:
    columns = exported_columns(schema, contract, table)
    kinds = {f["name"]: f["type"] for f in schema["fields"]}
    nullable = {f["name"]: bool(f["nullable"]) for f in schema["fields"]}
    def numeric(kind):
        return "{}, {}".format(*SQL_NUMERIC[kind]) if kind in SQL_NUMERIC else "NULL, NULL"
    declared = ",\n".join(
        f"    (N'{c}', {i}, N'{SQL_TYPE[kinds[c]]}', {numeric(kinds[c])}, {1 if nullable[c] else 0})"
        for i, c in enumerate(columns, 1))
    key = ", ".join(f"[{k}]" for k in schema["key"])
    rendered = [_render(c, kinds[c]) for c in columns]
    chunks = [rendered[i:i + CONCAT_CHUNK] for i in range(0, len(rendered), CONCAT_CHUNK)]
    for chunk in chunks:
        chunk[0] = f"CONVERT(nvarchar(max), {chunk[0]})"
    if len(chunks) == 1:
        expression = ",\n           ".join(chunks[0])
    else:
        expression = ",\n           ".join("CONCAT_WS(NCHAR(31),\n           " + ",\n           ".join(chunk) + ")" for chunk in chunks)
    text_columns = [c for c in columns if kinds[c] == "string"]
    reserved = "\n       OR ".join(
        f"DATALENGTH(REPLACE(REPLACE([{c}] COLLATE {COLLATION}, NCHAR(0), N''), NCHAR(31), N'')) <> DATALENGTH([{c}])"
        for c in text_columns)
    return f"""
-- ============================================================================================
-- {name}: structure, key, then the digest
-- ============================================================================================
IF OBJECT_ID(N'{name}', N'U') IS NULL
    INSERT INTO #result VALUES (N'{name}', N'table exists', N'a table', N'not found', NULL, 0);
ELSE
BEGIN
    -- 1. Structure. A digest cannot establish any of this. The variable name is fixed, so a
    -- loader that renames the table never touches it.
    DECLARE @declared TABLE (name sysname, ordinal int, type_name sysname,
                                     numeric_precision int, numeric_scale int, is_nullable bit);
    INSERT INTO @declared (name, ordinal, type_name, numeric_precision, numeric_scale, is_nullable) VALUES
{declared};

    INSERT INTO #result
    SELECT N'{name}', N'columns declared and in order', N'0 differences',
           CONVERT(nvarchar(200), COUNT(*)) + N' differences', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END
    FROM (
        -- Bound to the one object being checked by OBJECT_ID, never by name alone: a table of
        -- the same name in another schema must not be able to satisfy this.
        SELECT d.name FROM @declared d
        LEFT JOIN (SELECT c.name, c.column_id, t.name AS type_name, c.precision, c.scale, c.is_nullable
                   FROM sys.columns c JOIN sys.types t ON t.user_type_id = c.user_type_id
                   WHERE c.object_id = OBJECT_ID(N'{name}', N'U')) c
               ON c.name = d.name AND c.column_id = d.ordinal AND c.type_name = d.type_name
              AND (d.numeric_precision IS NULL
                   OR (c.precision = d.numeric_precision AND c.scale = d.numeric_scale))
              AND c.is_nullable = d.is_nullable
        WHERE c.name IS NULL
        UNION ALL
        SELECT c.name FROM sys.columns c
        WHERE c.object_id = OBJECT_ID(N'{name}', N'U')
          AND c.name NOT IN (SELECT name FROM @declared)
    ) AS differences;

    -- 2. The natural key: the digest is order independent, so a duplicated row and a missing
    -- one can cancel out.
    INSERT INTO #result
    SELECT N'{name}', N'natural key {key} unique and not null', N'0 offending rows',
           CONVERT(nvarchar(200), COUNT_BIG(*)) + N' offending rows', COUNT_BIG(*),
           CASE WHEN COUNT_BIG(*) = 0 THEN 1 ELSE 0 END
    FROM (SELECT {key} FROM {name} GROUP BY {key} HAVING COUNT_BIG(*) > 1) AS duplicates;

    -- 3. Reserved framing characters in the text columns.
    INSERT INTO #result
    SELECT N'{name}', N'no reserved framing characters in text', N'0 rows',
           CONVERT(nvarchar(200), COUNT_BIG(*)) + N' rows', COUNT_BIG(*),
           CASE WHEN COUNT_BIG(*) = 0 THEN 1 ELSE 0 END
    FROM {name}
    WHERE {reserved};

    -- 4. The row count and the digest, rendered as the CSV renders each row, NCHAR(0) for a
    -- null, fields joined with NCHAR(31) in contract order, hashed as UTF-8, the signed
    -- eight-byte prefixes summed as decimal.
    INSERT INTO #result
    SELECT N'{name}', N'row count', CONVERT(nvarchar(200), e.row_count),
           CONVERT(nvarchar(200), q.n), ABS(q.n - e.row_count),
           CASE WHEN q.n = e.row_count THEN 1 ELSE 0 END
    FROM #expected e CROSS JOIN (SELECT COUNT_BIG(*) AS n FROM {name}) AS q
    WHERE e.name = N'{name}';

    INSERT INTO #result
    SELECT N'{name}', N'row digest, definition version ' + CONVERT(nvarchar(10), e.digest_version),
           CONVERT(nvarchar(200), e.digest_total), CONVERT(nvarchar(200), ISNULL(q.total, 0)),
           CASE WHEN ISNULL(q.total, 0) = e.digest_total THEN 0 ELSE 1 END,
           CASE WHEN ISNULL(q.total, 0) = e.digest_total THEN 1 ELSE 0 END
    FROM #expected e CROSS JOIN (
        SELECT SUM(CONVERT(decimal(38,0), CONVERT(bigint, SUBSTRING(HASHBYTES('SHA2_256',
                   CONVERT(varchar(max), CONCAT_WS(NCHAR(31),
           {expression}) COLLATE {COLLATION})), 1, 8)))) AS total
        FROM {name}) AS q
    WHERE e.name = N'{name}';
END
"""


def _import_sql(table: str, name: str, schema: dict, contract: dict) -> str:
    columns = exported_columns(schema, contract, table)
    kinds = {f["name"]: f["type"] for f in schema["fields"]}
    nullable = {f["name"]: bool(f["nullable"]) for f in schema["fields"]}
    spec = contract["tables"][table]
    staging = ",\n    ".join(f"[{c}] varchar({STAGING_WIDTH}) COLLATE {COLLATION} NULL" for c in columns)
    typed = ",\n    ".join(
        f"[{c}] " + SQL_DECLARED.get(kinds[c], SQL_TYPE[kinds[c]]) + ("" if nullable[c] else " NOT NULL") for c in columns)
    key = ", ".join(f"[{k}]" for k in schema["key"])
    restore = []
    for c in columns:
        kind = kinds[c]
        if kind == "decimal":
            # Exact: only text that survives the round trip unchanged is converted; anything else
            # becomes NULL, which the presence check in check_loaded_digest.sql does not see but
            # the digest does, since the rendering of NULL differs from that of the value.
            decimal = SQL_DECLARED[kind]
            restore.append(f"CASE WHEN CONVERT(varchar({DECIMAL_TEXT}), CONVERT({decimal}, NULLIF([{c}], ''))) = [{c}] "
                           f"THEN CONVERT({decimal}, [{c}]) END")
        elif kind in ("int8", "int16", "int32"):
            # NULLIF: an empty string converts to 0, which the file never held.
            restore.append(f"CONVERT({SQL_TYPE[kind]}, NULLIF([{c}], ''))")
        else:
            restore.append(f"NULLIF([{c}], N'')")
    select = ",\n    ".join(restore)
    names = ",\n    ".join(f"[{c}]" for c in columns)
    return f"""
-- --------------------------------------------------------------------------------------------
-- {name}: stage as text, then restore the declared types. An empty cell is NULL; no AHAH
-- column is text that can be blank.
-- --------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS staging_{name};
CREATE TABLE staging_{name} (
    {staging}
);

-- EDIT the path. FORMAT = 'CSV' honours RFC 4180 quoting. ROWTERMINATOR is LF, as the
-- contract specifies. The UTF-8 encoding is declared on the staging columns' collation.
BULK INSERT staging_{name}
FROM '/path/to/{spec["file"][:-3]}'
WITH (FORMAT = 'CSV', FIELDQUOTE = '"', FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a',
      FIRSTROW = 2, TABLOCK);

DROP TABLE IF EXISTS {name};
CREATE TABLE {name} (
    {typed},
    CONSTRAINT PK_{name} PRIMARY KEY ({key})
);

INSERT INTO {name} (
    {names}
)
SELECT
    {select}
FROM staging_{name};

DROP TABLE IF EXISTS staging_{name};
"""


def render_import() -> str:
    contract = load_contract(CONTRACT)
    schema = load_schema(SCHEMA)
    return f"""-- Import the AHAH CSV into SQL Server, then check it with check_loaded_digest.sql.
-- Generated by python -m ahah_ingest.sql_check from the output schema and the export contract.
--
-- Decompress the file first and edit the path below. Run it against a database of your own:
-- it drops and recreates the two tables it names.
--
-- Verify the file hash against results/manifest.json before importing. After importing, run
-- check_loaded_digest.sql with that manifest's row count and digest total.

SET NOCOUNT ON;
SET XACT_ABORT ON;
{_import_sql(TABLE, TABLE, schema, contract)}"""


def render() -> str:
    contract = load_contract(CONTRACT)
    schema = load_schema(SCHEMA)
    digest = contract["digest"]
    return f"""-- Check the imported table against the build that produced its CSV.
-- Generated by python -m ahah_ingest.sql_check from the output schema and the export contract.
--
-- It reads the table; it never repairs, replaces or promotes anything. The expected values
-- come from results/manifest.json, which is the build's own record, never from the loaded table.
--
-- What this establishes: the declared columns, types, nullability and order are present, the
-- natural key is unique and not null, no text contains the framing characters, the row count
-- matches, and the recomputed digest matches.
-- What it does not: the digest truncates each SHA-256 to eight bytes and adds the results, so
-- collisions and cancelling changes are possible. It detects accidental load corruption.

SET NOCOUNT ON;
SET XACT_ABORT ON;

-- STEP 1. EDIT. Paste this build's numbers from results/manifest.json (csv.rows, csv.digest.total).
IF OBJECT_ID(N'tempdb..#expected', N'U') IS NOT NULL DROP TABLE #expected;
CREATE TABLE #expected (name sysname PRIMARY KEY, row_count bigint NOT NULL,
                        digest_total decimal(38,0) NOT NULL, digest_version int NOT NULL);
INSERT INTO #expected (name, row_count, digest_total, digest_version) VALUES
    (N'{TABLE}', 0, 0, {digest['version']})   -- EDIT: rows and total from manifest csv.digest
;

IF EXISTS (SELECT 1 FROM #expected WHERE digest_version <> {digest['version']})
    THROW 51000, 'This script implements digest definition version {digest['version']} only.', 1;
IF EXISTS (SELECT 1 FROM #expected WHERE row_count <= 0)
    THROW 51000, 'Expected row count and digest total have not been filled in from the manifest.', 1;

IF OBJECT_ID(N'tempdb..#result', N'U') IS NOT NULL DROP TABLE #result;
CREATE TABLE #result (table_name sysname, check_name nvarchar(200), expected nvarchar(200),
                      actual nvarchar(200), difference bigint NULL, passed bit NOT NULL);
{_table_sql(TABLE, TABLE, schema, contract)}
-- ============================================================================================
-- The result. A skipped check is not a pass, so an absent row fails the count below.
-- ============================================================================================
SELECT table_name, check_name, expected, actual, difference,
       CASE passed WHEN 1 THEN 'pass' ELSE 'FAIL' END AS outcome
FROM #result ORDER BY table_name, check_name;

DECLARE @failed int = (SELECT COUNT(*) FROM #result WHERE passed = 0);
DECLARE @ran int = (SELECT COUNT(*) FROM #result);
IF @failed > 0 OR @ran <> 5
    THROW 51000, 'The imported table does not match the build: see the result above.', 1;
"""


def main(argv=None) -> int:
    directory = Path(argv[0]) if argv else OUT.parent
    directory.mkdir(parents=True, exist_ok=True)
    for path, text in ((directory / IMPORT_OUT.name, render_import()), (directory / OUT.name, render())):
        path.write_text(text)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
