from __future__ import annotations

import pandas as pd
import pytest

from myproj.transform.trim_data import (
    filter_before_sea_level_start,
    select_columns,
)

# ── select_columns ────────────────────────────────────────────────────────────


def test_select_columns_returns_only_specified_columns():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    result = select_columns(df, ["a", "c"])
    assert list(result.columns) == ["a", "c"]


def test_select_columns_returns_copy():
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = select_columns(df, ["a"])
    result["a"] = 99
    assert df["a"].iloc[0] == 1


def test_select_columns_raises_for_missing_column():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="nicht vorhanden"):
        select_columns(df, ["a", "x"])


# ── filter_before_sea_level_start ─────────────────────────────────────────────


def _make_df(rows: list[tuple]) -> pd.DataFrame:
    """Helper: (year, month, day) rows."""
    return pd.DataFrame(rows, columns=["Start Year", "Start Month", "Start Day"])


def test_filter_removes_years_before_1999():
    df = _make_df([(1991, 6, 1), (1998, 12, 31)])
    assert filter_before_sea_level_start(df).empty


def test_filter_removes_january_1999():
    df = _make_df([(1999, 1, 15)])
    assert filter_before_sea_level_start(df).empty


def test_filter_removes_feb_1999_before_day_20():
    df = _make_df([(1999, 2, 1), (1999, 2, 19)])
    assert filter_before_sea_level_start(df).empty


def test_filter_keeps_feb_1999_day_20_and_later():
    df = _make_df([(1999, 2, 20), (1999, 2, 28)])
    assert len(filter_before_sea_level_start(df)) == 2


def test_filter_keeps_feb_1999_without_day():
    df = _make_df([(1999, 2, None)])
    assert len(filter_before_sea_level_start(df)) == 1


def test_filter_keeps_1999_without_month():
    df = _make_df([(1999, None, None)])
    assert len(filter_before_sea_level_start(df)) == 1


def test_filter_keeps_march_1999_and_later():
    df = _make_df([(1999, 3, 1), (1999, 12, 31), (2000, 1, 1)])
    assert len(filter_before_sea_level_start(df)) == 3


def test_filter_preserves_all_columns():
    df = pd.DataFrame(
        {
            "Start Year": [2000],
            "Start Month": [1],
            "Start Day": [1],
            "Country": ["Italy"],
        }
    )
    result = filter_before_sea_level_start(df)
    assert "Country" in result.columns
