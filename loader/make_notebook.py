"""Write loader/upload_ahah.ipynb, the notebook that loads the AHAH CSV into SQL Server from a
client machine through pyodbc, as the postcode-SIMD upload notebook does. It carries this
build's hash, row count and digest from results/manifest.json.

    python loader/make_notebook.py
"""

import json
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
from ahah_ingest.pipeline import verify_results
m = verify_results(ROOT / "results", files=True)     # refuses an interrupted promotion or a CSV the manifest does not describe
c = m["csv"]
built = m["built_at"][:10]

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md(f"""
# Load AHAH into SQL Server

**What this notebook does.** It loads `ahah_datazone`, the table of every AHAH edition for Scottish data
zones (build of {built}, 35,296 rows by 90 columns), into SQL Server from this machine through pyodbc,
proves the load is faithful with the digest the build recorded, and then shows the table in use: the twelve
columns HEAL-Scot asked for and the left join by data zone with its statuses.

**Before you start**

1. Put in one folder: `ahah_datazone.csv.gz` (or the unpacked `.csv`), `import_csv.sql` and
   `check_loaded_digest.sql` from `docs/sql/`.
2. Set `FOLDER`, `SERVER`, `DATABASE` and `TABLE` in step 1.
3. You need `CREATE TABLE` rights in the database. Step 1 tells you whether you have them.

**Run the cells in order, top to bottom.** Every step says what it does, what to expect and why.
""")

md("""
---
## Part 1. Set up

### Step 1. Settings, connection and files

**What it does.** Sets the folder, server, database and table; unpacks the CSV if only the archive is present;
lists the files it needs; connects and shows who you are connected as.

**What to expect.** Three lines starting `found`, then one row: server, database, your login,
`can_create_table = 1` and the SQL Server version (2019 or later is needed for the UTF-8 collation), then
`ready`. A missing file or a missing right raises here and nothing later runs.

**Why.** Every later step reads these files and this connection. Step 3 drops and recreates the table, so
the checks that would make it fail half way are made here, before anything is dropped.
""")
code("""
# Step 1 — settings, connection, permissions, files present
import hashlib, re, time
from pathlib import Path

import pandas as pd
import pyodbc

# EDIT: the folder holding the three files
FOLDER   = Path(r"")

SERVER   = "sql-de-01"
DATABASE = "IMD"
TABLE    = "dbo.ahah_datazone"      # one row per Scottish data zone per AHAH edition

DRIVER = "ODBC Driver 18 for SQL Server"
CONN = (f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")

# The CSV may arrive compressed: unpack it once, beside the archive.
packed = FOLDER / "ahah_datazone.csv.gz"
if not (FOLDER / "ahah_datazone.csv").is_file() and packed.is_file():
    import gzip, shutil
    print("unpacking", packed.name, "...")
    with gzip.open(packed, "rb") as src, open(FOLDER / "ahah_datazone.csv", "wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)

missing = []
for name in ["ahah_datazone.csv", "import_csv.sql", "check_loaded_digest.sql"]:
    path = FOLDER / name
    print(f"{'found   ' if path.is_file() else 'MISSING '} {name:28} "
          + (f"{path.stat().st_size:>13,} bytes" if path.is_file() else ""))
    if not path.is_file():
        missing.append(name)

# No connection pooling: every connect() is a fresh session, so nothing one cell leaves open can
# reach another. Read-only cells use autocommit=True: with the SQL Server driver, autocommit=False
# means implicit transactions, and a plain SELECT would open one.
pyodbc.pooling = False
with pyodbc.connect(CONN, timeout=10, autocommit=True) as cn:
    who = pd.read_sql(
        "SELECT @@SERVERNAME AS srv, DB_NAME() AS db, SUSER_NAME() AS login, "
        "HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE') AS can_create_table, "
        "CONVERT(varchar(20), SERVERPROPERTY('ProductVersion')) AS version", cn)
    display(who)

# Nothing later may run unless everything step 3 onward needs is here: step 3 drops the table.
if missing:
    raise FileNotFoundError(f"missing from {FOLDER}: {', '.join(missing)}")
if int(who.can_create_table[0]) != 1:
    raise PermissionError(f"{who.login[0]} cannot CREATE TABLE in {DATABASE}; ask for the right before running step 3")
print("ready")
""")

md(f"""
### Step 2. Is this exactly the file the build produced?

**What it does.** Hashes the CSV, counts its lines and reads its header, and compares them with what the
build of {built} recorded: SHA256 `{c['uncompressed_sha256'][:8]}…`, {c['uncompressed_bytes']:,} bytes,
{c['rows']:,} rows plus a header, {c['columns']} columns.

**What to expect.** `match` on the hash, the expected line and column counts, and the closing message. Any
mismatch stops the cell.

**Why.** A file can be truncated by a download or altered by being opened and saved in Excel, which would
round the 20-decimal values. Checking the hash first means nothing is loaded from a file that is not the
build's own. The digest total stored here is used again in step 5, inside SQL Server.
""")
code(f"""
# Step 2 — verify the transferred file against the build of {built}
EXPECTED = {{
    "csv":          "ahah_datazone.csv",
    "sha256":       "{c['uncompressed_sha256']}",
    "bytes":        {c['uncompressed_bytes']},
    "rows":         {c['rows']},
    "columns":      {c['columns']},
    "digest_total": "{c['digest']['total']}",   # checked in step 5, inside SQL Server
}}

path = FOLDER / EXPECTED["csv"]
digest, newlines = hashlib.sha256(), 0
with open(path, "rb") as fh:
    while True:
        block = fh.read(1 << 20)
        if not block:
            break
        digest.update(block)
        newlines += block.count(b"\\n")

header = pd.read_csv(path, nrows=0, dtype=str).columns.tolist()

print(f"size    {{path.stat().st_size:>13,}}   expected {{EXPECTED['bytes']:>13,}}")
print(f"sha256  {{digest.hexdigest()}}")
print(f"        {{EXPECTED['sha256']}}   {{'match' if digest.hexdigest() == EXPECTED['sha256'] else 'MISMATCH'}}")
print(f"lines   {{newlines:>13,}}   expected {{EXPECTED['rows'] + 1:>13,}}  (one header plus the rows)")
print(f"columns {{len(header):>13}}   expected {{EXPECTED['columns']:>13}}")
print(f"first three: {{header[:3]}}")
print(f"last three:  {{header[-3:]}}")

assert digest.hexdigest() == EXPECTED["sha256"], "the file is not the one this build produced"
assert newlines == EXPECTED["rows"] + 1 and len(header) == EXPECTED["columns"]
print("\\nthe file is exactly what the build wrote")
""")

md("""
---
## Part 2. Create and load the table

### Step 3. Create the table from the shipped definition

**What it does.** Takes the `CREATE TABLE ahah_datazone` statement from `import_csv.sql`, checks its columns
are exactly the CSV's header in the same order, then drops and recreates the table under your name, with the
primary key `(ahah_version, datazone_code)`.

**What to expect.** `90 columns`, then the type counts: decimal(38,20) 25, int 20, tinyint 21, smallint 22,
nvarchar(16) 2. A table showing 90 columns created, and the two key columns.

**Why.** The definition ships with the build and is tested against the schema, so using it rather than
writing one by hand guarantees the same types, nullability and key. `decimal(38,20)` holds every published
value exactly, up to 20 fractional digits. The drop and the create run in one transaction: if the create
fails, the previous table is still there.
""")
code("""
# Step 3 — create the table from the shipped definition
recipe = (FOLDER / "import_csv.sql").read_text(encoding="utf-8")

block = re.search(r"CREATE TABLE ahah_datazone \\((.*?)\\n\\);", recipe, re.S)
assert block, "could not find the table definition in import_csv.sql"

TYPES = dict(re.findall(r"\\[(\\w+)\\] (nvarchar\\(\\d+\\)|tinyint|smallint|int|decimal\\(\\d+,\\d+\\))", block.group(1)))
COLUMNS = list(TYPES)
assert COLUMNS == header, "the file's header does not match the shipped table definition"

bare = TABLE.split(".")[-1]
ddl = (block.group(0)
       .replace("CREATE TABLE ahah_datazone", f"CREATE TABLE {TABLE}")
       .replace("PK_ahah_datazone", f"PK_{bare}"))

print(f"{len(COLUMNS)} columns:", {t: sum(1 for v in TYPES.values() if v == t) for t in sorted(set(TYPES.values()))})
print(ddl.splitlines()[0]); print("   ..."); print("\\n".join(ddl.splitlines()[-2:]))

# One transaction: SQL Server DDL is transactional, so a failed CREATE rolls the DROP back and the
# previous table survives. autocommit stays off until both have succeeded.
with pyodbc.connect(CONN, timeout=30, autocommit=False) as cn:
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 120000;")          # a lock held elsewhere becomes an error after two minutes, not a silent wait
    try:
        cur.execute(f"DROP TABLE IF EXISTS {TABLE};")
        cur.execute(ddl)
    except Exception:
        cn.rollback()
        print(f"create failed; {TABLE} is as it was before this cell")
        raise
    cn.commit()
    cn.autocommit = True                              # the queries below must not open a new transaction
    display(pd.read_sql(
        f\"\"\"SELECT COUNT(*) AS columns_created,
                   SUM(CASE WHEN is_nullable = 1 THEN 1 ELSE 0 END) AS nullable
            FROM sys.columns WHERE object_id = OBJECT_ID('{TABLE}')\"\"\", cn))
    display(pd.read_sql(
        f\"\"\"SELECT i.name AS index_name, c.name AS key_column, ic.key_ordinal
            FROM sys.indexes i
            JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            JOIN sys.columns c ON c.object_id = i.object_id AND c.column_id = ic.column_id
            WHERE i.object_id = OBJECT_ID('{TABLE}') AND i.is_primary_key = 1
            ORDER BY ic.key_ordinal\"\"\", cn))
""")

md("""
### Step 4. Load the rows

**What it does.** Reads the CSV in chunks of 5,000 rows and inserts them, binding every value as text and
letting SQL Server convert it into the column's declared type. An empty cell becomes NULL in every column:
no AHAH column is text that can be blank, and a column an edition does not publish is NULL for it. Before
each chunk is sent, every decimal is checked to be in fixed notation with exactly 20 decimals, so SQL Server
cannot round anything on the way in.

**What to expect.** Progress every 10,000 rows, then `loaded 35,296 rows`, then one row: 35,296 rows in the
table, the NULL counts for three columns that only some editions have (`ur` 28,320 NULL, `domain_h_exp`
21,344 NULL, `greenspace_active` 20,928 NULL).

**Why.** The server cannot read this machine's files, so `BULK INSERT` is not available; sending the rows
from here is the alternative. Bound as text, an empty string would become 0 in an integer column, which
is why empties are sent as NULL.
""")
code("""
# Step 4 — load the rows, every empty cell as NULL, every decimal checked before it is sent
DECIMALS = [c for c, t in TYPES.items() if t.startswith("decimal")]
DECIMAL_TEXT = re.compile(r"^-?\\d{1,18}\\.\\d{20}$")

CHUNK = 5_000
insert = (f"INSERT INTO {TABLE} ([" + "], [".join(COLUMNS) + "]) "
          f"VALUES ({', '.join('?' * len(COLUMNS))})")

started, loaded = time.time(), 0
with pyodbc.connect(CONN, timeout=60) as cn:           # autocommit off: one commit per chunk
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 120000;")
    cur.fast_executemany = True
    cur.setinputsizes([(pyodbc.SQL_WVARCHAR, 64, 0)] * len(COLUMNS))
    for chunk in pd.read_csv(path, dtype=str, keep_default_na=False, chunksize=CHUNK, encoding="utf-8"):
        chunk = chunk.astype(object)
        for c in DECIMALS:
            bad = chunk[c].ne("") & ~chunk[c].str.match(DECIMAL_TEXT)
            assert not bad.any(), f"{c}: {chunk.loc[bad, c].iloc[0]!r} is not a 20-decimal value"
        for c in COLUMNS:
            chunk.loc[chunk[c].eq(""), c] = None
        cur.executemany(insert, chunk[COLUMNS].values.tolist())
        cn.commit()
        loaded += len(chunk)
        if loaded % 10_000 == 0 or loaded == EXPECTED["rows"]:
            print(f"  {loaded:>7,} rows   {loaded / (time.time() - started):>6,.0f} rows/s   {time.time() - started:>5.0f}s elapsed")

print(f"\\nloaded {loaded:,} rows in {time.time() - started:.0f}s")
with pyodbc.connect(CONN, timeout=30, autocommit=True) as cn:
    display(pd.read_sql(f\"\"\"
        SELECT COUNT_BIG(*) AS rows_in_table,
               SUM(CASE WHEN ur IS NULL THEN 1 ELSE 0 END)                AS ur_null,
               SUM(CASE WHEN domain_h_exp IS NULL THEN 1 ELSE 0 END)      AS domain_h_exp_null,
               SUM(CASE WHEN greenspace_active IS NULL THEN 1 ELSE 0 END) AS greenspace_active_null
        FROM {TABLE}\"\"\", cn))
""")

md("""
---
## Part 3. Prove the load is faithful

### Step 5. The digest, recomputed inside SQL Server

**What it does.** Runs the table section of `check_loaded_digest.sql` against your table: the column
structure (names, order, types including precision and scale, nullability, bound to this table's object),
the natural key, reserved characters in text, the row count, and a digest of every row compared with the
total the build recorded.

**What to expect.** Five checks, all `pass`.

**Why.** Steps 2 to 4 check the file and the mechanics; this checks the result. The digest renders each
loaded row exactly as the CSV wrote it and hashes it, so a single changed cell, a NULL loaded as 0, or a
decimal rounded on the way in makes it fail. It is the one check that compares the table in SQL Server
with the build.
""")
code("""
# Step 5 — recompute the digest inside SQL Server and compare it with the build
check = (FOLDER / "check_loaded_digest.sql").read_text(encoding="utf-8")

start = check.rindex("-- ===", 0, check.index("-- ahah_datazone: structure"))
end   = check.index("-- ===", check.index("END\\n", start))
section = check[start:end].replace("ahah_datazone", TABLE)

preamble = f\"\"\"
SET NOCOUNT ON;
DROP TABLE IF EXISTS #expected;
CREATE TABLE #expected (name sysname PRIMARY KEY, row_count bigint NOT NULL,
                        digest_total decimal(38,0) NOT NULL, digest_version int NOT NULL);
INSERT INTO #expected (name, row_count, digest_total, digest_version)
VALUES (N'{TABLE}', {EXPECTED["rows"]}, {EXPECTED["digest_total"]}, 1);
DROP TABLE IF EXISTS #result;
CREATE TABLE #result (table_name sysname, check_name nvarchar(200), expected nvarchar(200),
                      actual nvarchar(200), difference bigint NULL, passed bit NOT NULL);
\"\"\"

print("checking structure, key, framing characters, row count and digest ...")
started = time.time()
with pyodbc.connect(CONN, timeout=600, autocommit=True) as cn:
    cn.cursor().execute("SET LOCK_TIMEOUT 120000;")
    cn.cursor().execute(preamble + section)          # temp tables live for this connection
    outcome = pd.read_sql(
        \"\"\"SELECT check_name, expected, actual, difference,
                  CASE passed WHEN 1 THEN 'pass' ELSE 'FAIL' END AS outcome
           FROM #result ORDER BY check_name\"\"\", cn)
display(outcome)
print(f"{len(outcome)} checks in {time.time() - started:.0f}s")

assert len(outcome) == 5, "a check did not run, which is not the same as passing"
assert (outcome["outcome"] == "pass").all(), "the loaded table does not match the build"
print(f"\\nevery check passed: {TABLE} is the table the build produced")
""")

md("""
---
## Part 4. The table in use

### Step 6. Rows per edition, and the twelve HEAL-Scot columns

**What it does.** Counts rows per edition and vintage, then shows the twelve columns HEAL-Scot asked for
from version 4 for three zones: S01006506 (Culter 01), S01008132 (the zone whose air quality domain score is
exactly −1.0000, an ordinary value) and S01010206 (Petershill 04, which in version 2 has the −1 "no route" code).

**What to expect.** Five editions: 6,976 rows each on 2011 zones for 1 to 4, 7,392 on 2022 zones for 5.1.
Three rows of version 4 values; then the same zone in version 2 with `GP = -1` and `GP_dec = -1`.

**Why.** Rank 1 is the healthiest, the opposite of SIMD. The overall rank alone identifies the zone, so these
raw values stay inside the safe haven.
""")
code("""
# Step 6 — rows per edition, and the twelve HEAL-Scot columns of version 4
with pyodbc.connect(CONN, timeout=60, autocommit=True) as cn:
    display(pd.read_sql(f\"\"\"
        SELECT ahah_version, datazone_vintage, COUNT_BIG(*) AS rows, MIN(ahah_rnk) AS best_rank, MAX(ahah_rnk) AS worst_rank
        FROM {TABLE} GROUP BY ahah_version, datazone_vintage ORDER BY datazone_vintage, ahah_version\"\"\", cn))

    print("version 4, the twelve columns HEAL-Scot asked for")
    display(pd.read_sql(f\"\"\"
        SELECT datazone_code, dentist, GP, hospital, pharmacy, domain_h, domain_g, domain_e, domain_r, ahah, ahah_rnk, ahah_pct
        FROM {TABLE} WHERE ahah_version = '4' AND datazone_code IN ('S01006506', 'S01008132', 'S01010206')
        ORDER BY datazone_code\"\"\", cn))

    print("version 2, Petershill 04: the -1 no-route code in the routed indicators and their deciles")
    display(pd.read_sql(f\"\"\"
        SELECT datazone_code, GP, GP_dec, hospital, hospital_dec, NO2, NO2_dec, ur, domain_h_exp, ahah, ahah_rnk
        FROM {TABLE} WHERE ahah_version = '2' AND datazone_code = 'S01010206'\"\"\", cn))
""")

md("""
### Step 7. The left join by data zone

**What it does.** Builds a small temporary cohort with every kind of code a real extract can carry and joins
it to version 4 the way the README shows: a left join, trim and upper case only, and a status per row.

**What to expect.** Eight rows in, eight rows out: `matched` for S01006506, the padded lower-case
S01008132 and the repeated S01006506; `no_code` for NULL, empty and whitespace; `other_vintage` for the
2022 code S01013482; `not_a_datazone` for X99.

**Why.** No cohort row may disappear, and every row must say why it has no value. A 2022 code against
version 4 is the most likely mistake, and it is named rather than silently unmatched.
""")
code("""
# Step 7 — the left join by data zone, with its statuses
with pyodbc.connect(CONN, timeout=60, autocommit=True) as cn:
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 120000;")
    cur.execute(\"\"\"DROP TABLE IF EXISTS #cohort;
        CREATE TABLE #cohort (pseudo_id int, DataZone2011Code nvarchar(20) COLLATE DATABASE_DEFAULT);
        INSERT INTO #cohort VALUES (1, 'S01006506'), (2, NULL), (3, ''), (4, 'S01013482'),
                                   (5, 'X99'), (6, ' s01008132 '), (7, 'S01006506'), (8, '   ');\"\"\")
    out = pd.read_sql(f\"\"\"
        SELECT c.pseudo_id, a.ahah_rnk, a.ahah_pct, a.GP,
               CASE WHEN c.DataZone2011Code IS NULL OR LTRIM(RTRIM(c.DataZone2011Code)) = N'' THEN N'no_code'
                    WHEN a.datazone_code IS NOT NULL THEN N'matched'
                    WHEN v.datazone_code IS NOT NULL THEN N'other_vintage'
                    ELSE N'not_a_datazone' END AS ahah_status
        FROM #cohort AS c
        LEFT JOIN {TABLE} AS a ON a.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND a.ahah_version = N'4'
        LEFT JOIN {TABLE} AS v ON v.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND v.ahah_version = N'5.1'
        ORDER BY c.pseudo_id\"\"\", cn)
display(out)
assert len(out) == 8, "a cohort row disappeared or was duplicated"
assert out.ahah_status.tolist() == ["matched", "no_code", "no_code", "other_vintage",
                                    "not_a_datazone", "matched", "matched", "no_code"]
print("eight rows in, eight out, every status as expected")
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                                "language_info": {"name": "python"}})
out = ROOT / "loader" / "upload_ahah.ipynb"
nbf.write(nb, out)
print(f"wrote {out} ({len(cells)} cells)")
