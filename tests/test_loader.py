"""The loader's SQL filling, without a database: the default name and a schema-qualified one."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "docs" / "sql"


def load(tmp_path, table="ahah_datazone"):
    source = (ROOT / "loader" / "load_ahah_to_sqlserver.py").read_text()
    source = source.replace('MAIN_TABLE = "ahah_datazone"', f'MAIN_TABLE = "{table}"')
    source = source.replace('CSV_DIRECTORY = r"<C:\\path\\to\\the\\csv\\folder>"', f'CSV_DIRECTORY = r"{tmp_path}"')
    path = tmp_path / "loader.py"
    path.write_text(source)
    for name in ("import_csv.sql", "check_loaded_digest.sql"):
        (tmp_path / name).write_text((SQL / name).read_text())
    spec = importlib.util.spec_from_file_location("loader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rename_with_the_default_name_is_the_identity(tmp_path):
    m = load(tmp_path)
    text = (SQL / "check_loaded_digest.sql").read_text()
    assert m.rename_tables(text) == text


@pytest.mark.parametrize("table", ["ahah_datazone", "dbo.ahah_datazone", "geo.ahah_v1"])
def test_filled_scripts_carry_the_table_name_and_the_expectations(tmp_path, table):
    m = load(tmp_path, table)
    imp, chk = m.filled_import(), m.filled_check()
    schema, bare = m._parts(table)
    assert f"CREATE TABLE {schema}{bare} (" in imp and f"{schema}staging_{bare}" in imp and f"PK_{bare}" in imp
    assert f"FROM '{tmp_path}/ahah_datazone.csv'" in imp
    assert f"(N'{schema}{bare}', {m.EXPECTED['main']['rows']}, {m.EXPECTED['main']['digest_total']}, 1)" in chk
    assert f"OBJECT_ID(N'{schema}{bare}', N'U')" in chk
    # The local variable keeps a valid identifier whatever the table is called.
    assert "DECLARE @declared TABLE" in chk and "@declared_" not in chk and "@declared." not in chk
    assert "/path/to/" not in imp


def test_rename_leaves_the_file_name_alone(tmp_path):
    m = load(tmp_path, "dbo.ahah_datazone")
    assert "dbo.ahah_datazone.csv" not in m.filled_import()
