"""Compare every cell of the loaded SQL Server table with the original GeoDS files.

    python loader/compare_sql_with_sources.py "<ODBC connection string>" dbo.ahah_datazone data/sources ahah_ingest/mapping.yaml

Independent of the build: it reads the source CSVs with the csv module and Decimal, maps the
columns with mapping.yaml, pulls the whole table through pyodbc, and compares value by value.
A NULL must sit exactly where the edition has no column; a repeated key is a difference even
when the two rows are identical. Prints the counts and exits 1 on any difference.
"""

import csv
import sys
from decimal import Decimal
from pathlib import Path

FILES = {"1": "geods_previous/ahah_v1_fulldata.csv", "2": "geods_previous/ahah_v2_fulldata.csv",
         "3": "geods_previous/ahah_v3_fulldata.csv", "4": "geods_previous/ahah_v4.csv", "5.1": "geods/ahah_v5_1.csv"}


def compare(columns: list, rows, root: Path, mapping: dict, out=print) -> list:
    """`rows`: every physical row of the table, as sequences in `columns` order. Returns the
    differences; an empty list means every published cell equals its source and every other
    cell is NULL."""
    problems = []
    loaded = {}
    physical = 0
    for row in rows:
        physical += 1
        r = dict(zip(columns, row))
        key = (r["ahah_version"], r["datazone_code"])
        if key in loaded:
            problems.append((*key, "repeated key in the table"))
            continue
        loaded[key] = r
    out(f"{physical:,} physical rows read, {len(loaded):,} distinct keys")

    compared = nulls_checked = 0
    for version, rel in FILES.items():
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
                    problems.append((version, code, "missing in table"))
                    continue
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
            out(f"v{version}: {n:,} Scottish rows compared with {rel}")
    for key in loaded:
        problems.append((*key, "in table but not in any source file"))
    out(f"{compared:,} published cells compared, {nulls_checked:,} absent-edition cells checked for NULL, "
        f"{len(problems)} differences")
    for p in problems[:10]:
        out(f"   {p}")
    return problems


def main(argv) -> int:
    import pyodbc
    import yaml
    conn, table, root, mapping_path = argv
    mapping = yaml.safe_load(open(mapping_path))["editions"]
    cur = pyodbc.connect(conn, timeout=60).cursor()
    cur.execute(f"SELECT * FROM {table}")
    columns = [d[0] for d in cur.description]
    problems = compare(columns, cur.fetchall(), Path(root), mapping)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
