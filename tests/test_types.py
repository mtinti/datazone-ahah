"""The two new types and the writers: decimal and the nullable integers, rendered and read back.
The expectations are spelled out, not imported, so a change of convention is deliberate."""

from decimal import Decimal

import pandas as pd
import pytest

from ahah_ingest.core import output, text_output as tx
from ahah_ingest.core.checks import Report
from ahah_ingest.pipeline import CONTRACT


@pytest.fixture(scope="module")
def contract():
    return tx.load_contract(CONTRACT)


def tiny_schema():
    return {"version": "fixture", "table": "t", "key": ["k"], "sha256": "none",
            "fields": [{"name": "k", "type": "string", "nullable": False, "group": "key", "editions": [], "description": ""},
                       {"name": "score", "type": "decimal", "nullable": True, "group": "x", "editions": [], "description": ""},
                       {"name": "rank", "type": "int32", "nullable": True, "group": "x", "editions": [], "description": ""},
                       {"name": "flag", "type": "int8", "nullable": True, "group": "x", "editions": [], "description": ""}]}


def tiny_table():
    return pd.DataFrame({
        "k": pd.array(["A", "B", "C"], dtype="string"),
        "score": pd.Series([Decimal("2.36"), None, Decimal("6.225548837442603e-05")], dtype=object),
        "rank": pd.Series([1, 43064, None], dtype="Int64"),
        "flag": pd.Series([None, 0, 1], dtype="Int64"),
    })


def tiny_contract(contract):
    spec = dict(contract)
    spec["tables"] = {"t": {"file": "t.csv.gz", "exclude": []}}
    return spec


@pytest.mark.parametrize("text, expected", [
    ("2.36", "2.36000000000000000000"),
    ("6.225548837442603e-05", "0.00006225548837442603"),
    ("-1.0000", "-1.00000000000000000000"),
    ("-2.094345474", "-2.09434547400000000000"),
    ("0", "0.00000000000000000000"),
    ("-0.0", "0.00000000000000000000"),
    ("1E+2", "100.00000000000000000000"),
    ("123456789012345678.5", "123456789012345678.50000000000000000000"),
    ("0.00000000000000000001", "0.00000000000000000001"),
])
def test_decimal_renders_in_fixed_notation_with_twenty_places(text, expected):
    assert tx.render_decimal(tx.parse_decimal(text)) == expected
    assert tx.parse_decimal(expected) == tx.parse_decimal(text)


@pytest.mark.parametrize("text", ["1e-21", "1234567890123456789", "1.000000000000000000001", "NaN", "Infinity", "-Infinity"])
def test_decimal_that_does_not_fit_is_refused(text):
    with pytest.raises(tx.DecimalDoesNotFit):
        tx.render_decimal(tx.parse_decimal(text))


def test_decimal_is_never_parsed_through_a_float():
    assert tx.parse_decimal("0.1") + tx.parse_decimal("0.2") == Decimal("0.3")
    with pytest.raises(TypeError):
        tx.render_decimal(0.1)


def test_render_writes_each_type_and_marks_nulls(contract):
    spec = tiny_contract(contract)
    r = tx.render(tiny_table(), tiny_schema(), ["k", "score", "rank", "flag"], spec)
    marker = spec["digest"]["null_marker"]
    assert r["score"].tolist() == ["2.36000000000000000000", marker, "0.00006225548837442603"]
    assert r["rank"].tolist() == ["1", "43064", marker]
    assert r["flag"].tolist() == [marker, "0", "1"]


def test_nullable_integer_round_trips_null_zero_one_through_csv_parquet_and_digest(contract, tmp_path):
    """The round-3 finding: a NULL flag must stay NULL on every path."""
    spec = tiny_contract(contract)
    schema, table = tiny_schema(), tiny_table()
    rendered = tx.render(table, schema, ["k", "score", "rank", "flag"], spec)
    tx.write_csv(rendered, spec, tmp_path / "t.csv.gz")
    report = Report()
    tx.readback_csv(tmp_path / "t.csv.gz", rendered, spec, report, "csv")
    assert not report.blocking_failures
    import gzip
    text = gzip.open(tmp_path / "t.csv.gz", "rt").read()
    assert text.splitlines()[1] == "A,2.36000000000000000000,1,"
    output.write_table(table, schema, tmp_path / "t.parquet", {"x": "y"})
    saved = output.read_table(tmp_path / "t.parquet")
    assert saved["flag"].tolist()[0] is pd.NA and saved["flag"].tolist()[1:] == [0, 1]
    assert saved["score"].tolist()[0] == Decimal("2.36") and saved["score"].tolist()[1] is None
    # The digest tells a null from a zero.
    zero = table.copy()
    zero.loc[0, "flag"] = 0
    assert tx.row_digest(rendered, spec)["total"] != tx.row_digest(tx.render(zero, schema, list(rendered.columns), spec), spec)["total"]


def test_parquet_readback_compares_every_cell(contract, tmp_path):
    schema, table = tiny_schema(), tiny_table()
    output.write_table(table, schema, tmp_path / "t.parquet", {"x": "y"})
    report = Report()
    changed = table.copy()
    changed.loc[2, "score"] = Decimal("6.225548837442604e-05")
    output.readback(tmp_path / "t.parquet", schema, changed, {"x": "y"}, report)
    assert [c.name for c in report.blocking_failures] == ["readback.parquet.cells"]


def test_digest_is_order_independent_and_sees_one_changed_cell(contract):
    spec = tiny_contract(contract)
    schema = tiny_schema()
    rendered = tx.render(tiny_table(), schema, ["k", "score", "rank", "flag"], spec)
    shuffled = rendered.iloc[[2, 0, 1]]
    assert tx.row_digest(rendered, spec)["total"] == tx.row_digest(shuffled, spec)["total"]
    changed = tiny_table()
    changed.loc[0, "rank"] = 2
    assert tx.row_digest(tx.render(changed, schema, list(rendered.columns), spec), spec)["total"] != tx.row_digest(rendered, spec)["total"]


def test_reserved_characters_are_refused(contract):
    spec = tiny_contract(contract)
    table = tiny_table()
    table.loc[0, "k"] = "A\x1fB"
    with pytest.raises(tx.ReservedCharacter):
        tx.render(table, tiny_schema(), ["k"], spec)


def test_csv_readback_catches_a_changed_cell(contract, tmp_path):
    spec = tiny_contract(contract)
    rendered = tx.render(tiny_table(), tiny_schema(), ["k", "score", "rank", "flag"], spec)
    tx.write_csv(rendered, spec, tmp_path / "t.csv.gz")
    changed = rendered.copy()
    changed.loc[1, "rank"] = "43065"
    report = Report()
    tx.readback_csv(tmp_path / "t.csv.gz", changed, spec, report, "csv")
    assert [c.name for c in report.blocking_failures] == ["csv.cells"]
