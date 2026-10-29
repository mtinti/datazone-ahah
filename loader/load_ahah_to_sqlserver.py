"""Load the AHAH CSV into SQL Server and check that the load is faithful.

Carry four files to the machine that will run this: the CSV (ahah_datazone.csv or its .gz),
the two SQL scripts from docs/sql (import_csv.sql and check_loaded_digest.sql), and this file.
Put them in one folder, fill in the block marked EDIT below, and run:

    python load_ahah_to_sqlserver.py                 # verify, import, check
    python load_ahah_to_sqlserver.py --check-only    # only re-run the checks
    python load_ahah_to_sqlserver.py --print-sql     # write the filled SQL, connect to nothing

Built on 2026-10-29 from AHAH editions 1, 2, 3, 4 and 5.1. The expected hash, row count
and digest below belong to that build; a later build needs a new copy of this script.

It connects with Windows integrated authentication unless you paste an ODBC connection string.
No password is stored here. If a password is unavoidable, pass it in the environment as
AHAH_SQL_PASSWORD together with AHAH_SQL_USER, and it is used without being written anywhere.
"""

from __future__ import annotations

# =================================================================================================
# EDIT: everything this script needs to know about your server.
# =================================================================================================

SERVER = r"<SERVER\INSTANCE>"          # for example  r"NHSSQL01\PROD,1433"
DATABASE = r"<DATABASE>"               # it must already exist; this script does not create it

MAIN_TABLE = "ahah_datazone"           # one row per Scottish data zone per AHAH edition

# The folder holding the CSV file, as this machine sees it.
CSV_DIRECTORY = r"<C:\path\to\the\csv\folder>"

# The same folder as the SQL Server sees it. BULK INSERT reads from the server's own filesystem.
SERVER_CSV_DIRECTORY = CSV_DIRECTORY

# Leave empty for Windows integrated authentication, or paste your site's own string whole.
ODBC_CONNECTION_STRING = ""

# =================================================================================================
# Nothing below needs editing.
# =================================================================================================

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BUILD = {"built_at": "2026-10-29T20:10:13Z", "schema_version": "ahah_datazone_v1"}

# What the build recorded (results/manifest.json). The digest total is what the check script
# compares against, and it comes from here rather than from the loaded table.
EXPECTED = {
    "main": {
        "csv": "ahah_datazone.csv",
        "sha256": "11351af109e574017a8d00f493d044dd92942f42c72624fa0c4efe054da6d5d8",
        "bytes": 22037911, "rows": 35296, "columns": 90,
        "digest_total": "1313739416145945439820",
        "gz": "ahah_datazone.csv.gz",
        "gz_sha256": "505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574",
    },
}
GENERATED_NAMES = {"main": "ahah_datazone"}


def fail(message: str) -> None:
    sys.exit("stopped: " + message)


def check_settings() -> None:
    for name, value in (("SERVER", SERVER), ("DATABASE", DATABASE), ("CSV_DIRECTORY", CSV_DIRECTORY)):
        if "<" in str(value):
            fail(f"{name} is still a placeholder. Fill in the EDIT block at the top of this file.")
    if not Path(CSV_DIRECTORY).is_dir():
        fail(f"CSV_DIRECTORY does not exist: {CSV_DIRECTORY}")
    for name in ("import_csv.sql", "check_loaded_digest.sql"):
        if not (HERE / name).is_file():
            fail(f"{name} is not beside this script. Copy it from docs/sql in the project.")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_files() -> None:
    """The files travelled, so check them before they reach the database. The compressed form
    is what usually travels, so decompress it here if only that is present."""
    for table, expected in EXPECTED.items():
        path = Path(CSV_DIRECTORY) / expected["csv"]
        packed = Path(CSV_DIRECTORY) / expected["gz"]
        if not path.is_file() and packed.is_file():
            actual = sha256(packed)
            if actual != expected["gz_sha256"]:
                fail(f"{expected['gz']}: expected sha256 {expected['gz_sha256'][:16]}, found {actual[:16]}")
            print(f"  {expected['gz']}: sha256 matches, decompressing")
            import gzip
            with gzip.open(packed, "rb") as source, path.open("wb") as target:
                while True:
                    block = source.read(1 << 20)
                    if not block:
                        break
                    target.write(block)
        if not path.is_file():
            fail(f"neither {expected['csv']} nor {expected['gz']} is in {CSV_DIRECTORY}")
        size = path.stat().st_size
        if size != expected["bytes"]:
            fail(f"{expected['csv']}: expected {expected['bytes']:,} bytes, found {size:,}. "
                 "A transfer that changed the line endings will do this.")
        actual = sha256(path)
        if actual != expected["sha256"]:
            fail(f"{expected['csv']}: expected sha256 {expected['sha256'][:16]}, found {actual[:16]}")
        print(f"  {expected['csv']}: {size:,} bytes, sha256 matches, "
              f"{expected['rows']:,} rows x {expected['columns']} columns")


def _parts(name: str) -> tuple:
    """A schema prefix and the bare table name, so derived identifiers stay valid: a staging
    table belongs in the same schema, and a constraint name cannot contain a dot."""
    clean = name.replace("[", "").replace("]", "").strip()
    if "." in clean:
        schema, bare = clean.rsplit(".", 1)
        return schema + ".", bare
    return "", clean


def rename_tables(sql: str) -> str:
    """Put your table names into the generated scripts.

    Every replacement is parked on a marker first, because the default history name contains
    the default main name, and because the CSV file names contain both.
    """
    replacements = []
    for key, chosen in (("main", MAIN_TABLE),):
        generated = GENERATED_NAMES[key]
        schema, bare = _parts(chosen)
        # Longest first: the staging and constraint names contain the table name.
        replacements += [(f"staging_{generated}", f"{schema}staging_{bare}"),
                         (f"PK_{generated}", f"PK_{bare}"),
                         (f"{generated}.csv", f"\x01{key}csv\x01"),   # a file name, not an identifier
                         (generated, f"{schema}{bare}")]
    parked = {}
    for n, (old, new) in enumerate(replacements):
        marker = f"\x00{n}\x00"
        parked[marker] = new
        sql = sql.replace(old, marker)
    for marker, new in parked.items():
        sql = sql.replace(marker, new)
    # The file names were parked twice over, so put them back last and unchanged.
    for key in GENERATED_NAMES:
        sql = sql.replace(f"\x01{key}csv\x01", f"{GENERATED_NAMES[key]}.csv")
    return sql


def filled_import() -> str:
    sql = rename_tables((HERE / "import_csv.sql").read_text(encoding="utf-8"))
    separator = "\\" if "\\" in SERVER_CSV_DIRECTORY else "/"
    for expected in EXPECTED.values():
        target = SERVER_CSV_DIRECTORY.rstrip("/\\") + separator + expected["csv"]
        sql = sql.replace(f"/path/to/{expected['csv']}", target)
    if "/path/to/" in sql:
        fail("a CSV path was not filled in; the import script may not be the one this build shipped")
    return sql


def filled_check() -> str:
    sql = (HERE / "check_loaded_digest.sql").read_text(encoding="utf-8")
    for table, expected in EXPECTED.items():
        placeholder = f"(N'{GENERATED_NAMES[table]}', 0, 0, "
        if placeholder not in sql:
            fail(f"the check script has no place to put the expectations for {table}")
        sql = sql.replace(placeholder, f"(N'{GENERATED_NAMES[table]}', {expected['rows']}, "
                                       f"{expected['digest_total']}, ")
    return rename_tables(sql)


def connection_string() -> str:
    if ODBC_CONNECTION_STRING:
        return ODBC_CONNECTION_STRING
    parts = [r"Driver={ODBC Driver 18 for SQL Server}", f"Server={SERVER}", f"Database={DATABASE}",
             "Encrypt=yes", "TrustServerCertificate=yes"]
    user = os.environ.get("AHAH_SQL_USER")
    if user:
        password = os.environ.get("AHAH_SQL_PASSWORD")
        if not password:
            fail("AHAH_SQL_USER is set but AHAH_SQL_PASSWORD is not")
        parts += [f"UID={user}", f"PWD={password}"]
    else:
        parts.append("Trusted_Connection=yes")
    return ";".join(parts) + ";"


def run(sql: str, label: str) -> None:
    """Run one script, preferring pyodbc and falling back to sqlcmd."""
    try:
        import pyodbc
    except ImportError:
        pyodbc = None
    if pyodbc is not None:
        with pyodbc.connect(connection_string(), autocommit=True) as connection:
            cursor = connection.cursor()
            for batch in re.split(r"(?im)^\s*GO\s*$", sql):
                if batch.strip():
                    cursor.execute(batch)
                    while True:
                        if cursor.description:
                            rows = cursor.fetchall()
                            for row in rows:
                                print("   " + " | ".join("" if v is None else str(v) for v in row))
                        if not cursor.nextset():
                            break
        return
    written = HERE / f"{label}.filled.sql"
    written.write_text(sql, encoding="utf-8")
    command = ["sqlcmd", "-S", SERVER, "-d", DATABASE, "-b", "-I", "-C", "-i", str(written)]
    user = os.environ.get("AHAH_SQL_USER")
    command += ["-U", user, "-P", os.environ["AHAH_SQL_PASSWORD"]] if user else ["-E"]
    done = subprocess.run(command, capture_output=True, text=True)
    print(done.stdout.strip())
    if done.stderr.strip():
        print(done.stderr.strip(), file=sys.stderr)
    if done.returncode != 0:
        fail(f"sqlcmd returned {done.returncode} for {label}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check-only", action="store_true", help="skip the import, run the checks")
    parser.add_argument("--print-sql", action="store_true",
                        help="write the filled scripts beside this file and connect to nothing")
    args = parser.parse_args()

    check_settings()
    print(f"build {BUILD['built_at']}, schema {BUILD['schema_version']}")
    print(f"target {SERVER} / {DATABASE}: {MAIN_TABLE}")

    if args.print_sql:
        for label, sql in (("import_csv", filled_import()), ("check_loaded_digest", filled_check())):
            path = HERE / f"{label}.filled.sql"
            path.write_text(sql, encoding="utf-8")
            print(f"  wrote {path}")
        print("nothing was connected to or loaded")
        return 0

    print("verifying the files that were transferred")
    verify_files()
    if not args.check_only:
        print("importing, which drops and recreates the table")
        run(filled_import(), "import_csv")
    print("checking the loaded table against the build")
    run(filled_check(), "check_loaded_digest")
    print("done. Every check above must say pass; the script raises an error if one does not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
