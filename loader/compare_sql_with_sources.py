"""Compare every cell of the loaded SQL Server table with the original GeoDS files.

    python loader/compare_sql_with_sources.py "<ODBC connection string>" dbo.ahah_datazone data/sources ahah_ingest/mapping.yaml

Independent of the build: it reads the source CSVs with the csv module and Decimal, maps the
columns with mapping.yaml, pulls the whole table through pyodbc, and compares value by value.
A NULL must sit exactly where the edition has no column. Prints the counts and exits 1 on any
difference.
"""

import csv
import sys
from decimal import Decimal
from pathlib import Path

import pyodbc
import yaml

conn, table, root, mapping_path = sys.argv[1], sys.argv[2], Path(sys.argv[3]), sys.argv[4]
mapping = yaml.safe_load(open(mapping_path))["editions"]
files = {"1": "geods_previous/ahah_v1_fulldata.csv", "2": "geods_previous/ahah_v2_fulldata.csv",
         "3": "geods_previous/ahah_v3_fulldata.csv", "4": "geods_previous/ahah_v4.csv", "5.1": "geods/ahah_v5_1.csv"}

cn = pyodbc.connect(conn, timeout=60)
cur = cn.cursor()
cur.execute(f"SELECT * FROM {table}")
columns = [d[0] for d in cur.description]
loaded = {}
for row in cur.fetchall():
    r = dict(zip(columns, row))
    loaded[(r["ahah_version"], r["datazone_code"])] = r
print(f"{len(loaded):,} rows read from {table}")

compared = nulls_checked = 0
problems = []
for version, rel in files.items():
    m = mapping[version]
    with open(root / rel, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        code_col = reader.fieldnames[0]
        n = 0
        for src in reader:
            code = src[code_col]
            if not code.startswith("S01"):
                continue
            n += 1
            got = loaded.pop((version, code), None)
            if got is None:
                problems.append((version, code, "missing in table")); continue
            mapped = set()
            for file_col, table_col in m.items():
                mapped.add(table_col)
                text, value = src[file_col], got[table_col]
                if table_col == "datazone_code":
                    ok = value == text
                elif isinstance(value, Decimal):
                    ok = value == Decimal(text)
                elif isinstance(value, int):
                    ok = Decimal(text) == value
                else:
                    ok = False
                compared += 1
                if not ok:
                    problems.append((version, code, table_col, text, value))
            for table_col in columns:
                if table_col in mapped or table_col in ("ahah_version", "datazone_vintage"):
                    continue
                nulls_checked += 1
                if got[table_col] is not None:
                    problems.append((version, code, table_col, "expected NULL", got[table_col]))
            if got["datazone_vintage"] != (2022 if version == "5.1" else 2011):
                problems.append((version, code, "datazone_vintage", got["datazone_vintage"]))
        print(f"v{version}: {n:,} Scottish rows compared with {rel}")
for key in loaded:
    problems.append((key, "in table but not in any source file"))
print(f"{compared:,} published cells compared, {nulls_checked:,} absent-edition cells checked for NULL, {len(problems)} differences")
for p in problems[:10]:
    print("  ", p)
sys.exit(1 if problems else 0)
