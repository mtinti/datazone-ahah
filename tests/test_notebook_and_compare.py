"""The upload notebook's guards and the comparison command, against a fake pyodbc: the notebook
must refuse to run before dropping anything, must keep the previous table when CREATE fails,
and the comparison must report a repeated key even when the rows are identical."""

import importlib.util
import json
import numbers
import sys
import types
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "loader" / "upload_ahah.ipynb"
SQL = ROOT / "docs" / "sql"


def cell_source(step: int) -> str:
    nb = json.loads(NOTEBOOK.read_text())
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            src = "".join(c["source"])
            if src.startswith(f"# Step {step} "):
                return src
    raise KeyError(step)


class FakeCursor:
    def __init__(self, conn, fail_on=None):
        self.conn, self.fail_on, self.executed = conn, fail_on, []

    def execute(self, sql, *args):
        self.executed.append(sql)
        self.conn.log.append(sql)
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("CREATE TABLE permission denied")
        return self


class FakeConnection:
    def __init__(self, log, fail_on=None, autocommit=True):
        self.log, self.fail_on, self.autocommit = log, fail_on, autocommit
        self.rolled_back = self.committed = False

    def cursor(self):
        return FakeCursor(self, self.fail_on)

    def rollback(self):
        self.rolled_back = True
        self.log.append("ROLLBACK")

    def commit(self):
        self.committed = True
        self.log.append("COMMIT")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_pyodbc(log, fail_on=None, can_create=1):
    module = types.ModuleType("pyodbc")
    module.SQL_WVARCHAR = 0
    module.connect = lambda conn, **kw: FakeConnection(log, fail_on, kw.get("autocommit", True))
    frames = {"can_create_table": pd.DataFrame({"srv": ["s"], "db": ["d"], "login": ["me"], "can_create_table": [can_create], "version": ["16"]}),
              "columns_created": pd.DataFrame({"columns_created": [90], "nullable": [87]}),
              "index_name": pd.DataFrame({"index_name": [], "key_column": [], "key_ordinal": []})}
    def read_sql(sql, cn, **kw):
        for key, frame in frames.items():
            if key in sql:
                return frame
        raise AssertionError(sql)
    return module, read_sql


def run_step(step, folder, log, monkeypatch, **kw):
    module, read_sql = fake_pyodbc(log, **kw)
    monkeypatch.setitem(sys.modules, "pyodbc", module)
    monkeypatch.setattr(pd, "read_sql", read_sql)
    env = {"display": lambda df: None, "__name__": "nb"}
    exec(f'FOLDER = __import__("pathlib").Path(r"{folder}")\n', env)
    exec(cell_source(1).replace('FOLDER   = Path(r"")', 'FOLDER = FOLDER'), env)
    if step >= 2:
        exec(cell_source(2), env)
    if step >= 3:
        exec(cell_source(3), env)
    return env


@pytest.fixture
def delivery(tmp_path):
    import gzip
    with gzip.open(ROOT / "results" / "ahah_datazone.csv.gz", "rb") as src:
        (tmp_path / "ahah_datazone.csv").write_bytes(src.read())
    for name in ("import_csv.sql", "check_loaded_digest.sql"):
        (tmp_path / name).write_text((SQL / name).read_text())
    return tmp_path


def test_missing_file_stops_step_1_before_any_sql_that_drops(delivery, monkeypatch):
    (delivery / "check_loaded_digest.sql").unlink()
    log = []
    with pytest.raises(FileNotFoundError, match="check_loaded_digest.sql"):
        run_step(1, delivery, log, monkeypatch)
    assert not any("DROP" in s for s in log)


def test_missing_create_right_stops_step_1(delivery, monkeypatch):
    log = []
    with pytest.raises(PermissionError, match="CREATE TABLE"):
        run_step(1, delivery, log, monkeypatch, can_create=0)
    assert not any("DROP" in s for s in log)


def test_failed_create_rolls_the_drop_back(delivery, monkeypatch):
    log = []
    with pytest.raises(RuntimeError, match="permission denied"):
        run_step(3, delivery, log, monkeypatch, fail_on="CREATE TABLE")
    drop = next(i for i, s in enumerate(log) if "DROP TABLE" in s)
    assert "ROLLBACK" in log[drop:] and "COMMIT" not in log


def test_successful_create_commits_once(delivery, monkeypatch):
    log = []
    run_step(3, delivery, log, monkeypatch)
    assert log.count("COMMIT") == 1 and "ROLLBACK" not in log
    assert log.index("COMMIT") > max(i for i, s in enumerate(log) if "CREATE TABLE" in s)


def load_compare():
    spec = importlib.util.spec_from_file_location("compare", ROOT / "loader" / "compare_sql_with_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HAVE_FILES = all((ROOT / "data" / "sources" / rel).is_file() for rel in
                 ("geods/ahah_v5_1.csv", "geods_previous/ahah_v4.csv", "geods_previous/ahah_v1_fulldata.csv"))


@pytest.mark.skipif(not HAVE_FILES, reason="pinned source files not present")
def test_comparison_reports_an_identical_duplicate_and_a_changed_cell():
    import yaml
    from ahah_ingest.core.output import read_table
    compare = load_compare()
    table = read_table(ROOT / "results" / "ahah_datazone.parquet")
    columns = list(table.columns)
    # As pyodbc would hand them over: None, int, Decimal or str.
    rows = [tuple(None if v is pd.NA or v is None else int(v) if isinstance(v, numbers.Integral) else v for v in r)
            for r in table.itertuples(index=False)]
    mapping = yaml.safe_load(open(ROOT / "ahah_ingest" / "mapping.yaml"))["editions"]
    quiet = lambda *a, **k: None
    assert compare.compare(columns, rows, ROOT / "data" / "sources", mapping, out=quiet) == []
    # An identical duplicate row is a difference.
    dup = rows + [rows[0]]
    problems = compare.compare(columns, dup, ROOT / "data" / "sources", mapping, out=quiet)
    assert problems == [(rows[0][0], rows[0][2], "repeated key in the table")]
    # A changed cell, and a value where NULL is expected.
    gp = columns.index("GP")
    changed = list(rows)
    changed[0] = tuple(Decimal("0.5") if i == gp else v for i, v in enumerate(rows[0]))
    problems = compare.compare(columns, changed, ROOT / "data" / "sources", mapping, out=quiet)
    assert len(problems) == 1 and problems[0][2] == "GP"
