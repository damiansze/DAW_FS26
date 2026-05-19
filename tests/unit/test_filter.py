from __future__ import annotations

import pandas as pd
import pytest

from myproj.transform.filter import (
    filter_to_floods,
    filter_to_mediterranean,
    filter_to_sea_level_coverage,
    select_columns,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_emdat(rows: list[tuple]) -> pd.DataFrame:
    """Helper: (year, month, day) rows."""
    return pd.DataFrame(rows, columns=["Start Year", "Start Month", "Start Day"])


def _make_sea_level(start: str, end: str) -> pd.DataFrame:
    """Sea level DataFrame spanning from start to end date."""
    return pd.DataFrame({"time": pd.date_range(start, end, freq="D")})


def _make_disaster_df(rows: list[dict]) -> pd.DataFrame:
    defaults = {"Disaster Type": "", "Disaster Subtype": ""}
    return pd.DataFrame([{**defaults, **r} for r in rows])


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


# ── filter_to_sea_level_coverage ──────────────────────────────────────────────


def test_coverage_removes_events_before_sea_level_start():
    df = _make_emdat([(1991, 6, 1), (1998, 12, 31)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert filter_to_sea_level_coverage(df, sea).empty


def test_coverage_removes_events_after_sea_level_end():
    df = _make_emdat([(2025, 1, 1)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert filter_to_sea_level_coverage(df, sea).empty


def test_coverage_keeps_events_within_range():
    df = _make_emdat([(2000, 6, 1), (2010, 3, 15)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert len(filter_to_sea_level_coverage(df, sea)) == 2


def test_coverage_event_exactly_on_start_date_is_kept():
    df = _make_emdat([(1999, 2, 20)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert len(filter_to_sea_level_coverage(df, sea)) == 1


def test_coverage_event_one_day_before_start_is_removed():
    df = _make_emdat([(1999, 2, 19)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert filter_to_sea_level_coverage(df, sea).empty


def test_coverage_missing_month_uses_pessimistic_lower_bound():
    # fillna(1) for month → date_lower = 1999-01-01 < 1999-02-20 → removed
    df = _make_emdat([(1999, None, None)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert filter_to_sea_level_coverage(df, sea).empty


def test_coverage_missing_month_in_safe_year_is_kept():
    # date_lower = 2000-01-01 >= 1999-02-20, date_upper = 2000-12-28 <= 2024-12-31
    df = _make_emdat([(2000, None, None)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    assert len(filter_to_sea_level_coverage(df, sea)) == 1


def test_coverage_preserves_all_columns():
    df = pd.DataFrame(
        {
            "Start Year": [2000],
            "Start Month": [1],
            "Start Day": [1],
            "Country": ["Italy"],
        }
    )
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    result = filter_to_sea_level_coverage(df, sea)
    assert "Country" in result.columns


def test_coverage_returns_copy():
    df = _make_emdat([(2000, 1, 1)])
    sea = _make_sea_level("1999-02-20", "2024-12-31")
    result = filter_to_sea_level_coverage(df, sea)
    result["Start Year"] = 9999
    assert df["Start Year"].iloc[0] == 2000


# ── filter_to_floods ──────────────────────────────────────────────────────────


def test_filter_to_floods_keeps_flood_disaster_type():
    df = _make_disaster_df([{"Disaster Type": "Flood"}])
    assert len(filter_to_floods(df)) == 1


def test_filter_to_floods_keeps_flood_in_subtype():
    df = _make_disaster_df([{"Disaster Type": "Storm", "Disaster Subtype": "Flash Flood"}])
    assert len(filter_to_floods(df)) == 1


def test_filter_to_floods_removes_non_flood():
    df = _make_disaster_df([{"Disaster Type": "Earthquake", "Disaster Subtype": "Ground movement"}])
    assert filter_to_floods(df).empty


def test_filter_to_floods_is_case_insensitive():
    df = _make_disaster_df([{"Disaster Type": "FLOOD"}, {"Disaster Type": "flood"}])
    assert len(filter_to_floods(df)) == 2


def test_filter_to_floods_returns_copy():
    df = _make_disaster_df([{"Disaster Type": "Flood"}])
    result = filter_to_floods(df)
    result["Disaster Type"] = "X"
    assert df["Disaster Type"].iloc[0] == "Flood"


# ── filter_to_mediterranean ───────────────────────────────────────────────────


def test_filter_to_mediterranean_keeps_med_countries():
    df = pd.DataFrame({"ISO": ["ITA", "FRA", "GRC"]})
    assert len(filter_to_mediterranean(df)) == 3


def test_filter_to_mediterranean_removes_non_med():
    df = pd.DataFrame({"ISO": ["DEU", "USA", "CHN"]})
    assert filter_to_mediterranean(df).empty


def test_filter_to_mediterranean_mixed():
    df = pd.DataFrame({"ISO": ["ITA", "DEU", "ESP"]})
    result = filter_to_mediterranean(df)
    assert list(result["ISO"]) == ["ITA", "ESP"]


def test_filter_to_mediterranean_returns_copy():
    df = pd.DataFrame({"ISO": ["ITA"]})
    result = filter_to_mediterranean(df)
    result["ISO"] = "X"
    assert df["ISO"].iloc[0] == "ITA"
