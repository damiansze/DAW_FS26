from __future__ import annotations

import pandas as pd
import pytest

from myproj.link.join import (
    drop_join_redundant_cols,
    join_sea_level,
    prepare_sea_level_ts,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_sea_level(values: list[float], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.to_datetime(dates),
            "MSL_filtered_GIA_corrected_adjusted": values,
            "trend_MSL_filtered_GIA_corrected_adjusted": [0.0] * len(values),
        }
    )


def _make_daily_sea_level(start: str, end: str, value: float = 10.0) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame(
        {
            "time": dates,
            "MSL_filtered_GIA_corrected_adjusted": [value] * len(dates),
            "trend_MSL_filtered_GIA_corrected_adjusted": [0.0] * len(dates),
        }
    )


def _make_flood_df(start: str, end: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start_date": pd.to_datetime([start]),
            "end_date": pd.to_datetime([end]),
        }
    )


# ── prepare_sea_level_ts ──────────────────────────────────────────────────────


def test_prepare_sea_level_ts_converts_time_to_datetime():
    sea = pd.DataFrame({"time": ["2005-01-01", "2005-01-02"]})
    result = prepare_sea_level_ts(sea)
    assert pd.api.types.is_datetime64_any_dtype(result["time"])


def test_prepare_sea_level_ts_sorts_by_time():
    sea = pd.DataFrame({"time": pd.to_datetime(["2005-01-03", "2005-01-01", "2005-01-02"])})
    result = prepare_sea_level_ts(sea)
    assert list(result["time"]) == list(pd.to_datetime(["2005-01-01", "2005-01-02", "2005-01-03"]))


def test_prepare_sea_level_ts_resets_index():
    sea = pd.DataFrame({"time": pd.to_datetime(["2005-01-03", "2005-01-01"])})
    result = prepare_sea_level_ts(sea)
    assert list(result.index) == [0, 1]


def test_prepare_sea_level_ts_returns_copy():
    sea = pd.DataFrame({"time": pd.to_datetime(["2005-01-01"])})
    result = prepare_sea_level_ts(sea)
    result["time"] = pd.Timestamp("2000-01-01")
    assert sea["time"].iloc[0] == pd.Timestamp("2005-01-01")


# ── join_sea_level ────────────────────────────────────────────────────────────


def test_join_sea_level_adds_sea_level_at_start():
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31", value=5.0)
    df = _make_flood_df("2005-06-01", "2005-06-10")
    result = join_sea_level(df, sea)
    assert "sea_level_at_start" in result.columns
    assert result["sea_level_at_start"].iloc[0] == pytest.approx(5.0)


def test_join_sea_level_adds_sea_level_at_end():
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31", value=5.0)
    df = _make_flood_df("2005-06-01", "2005-06-10")
    result = join_sea_level(df, sea)
    assert "sea_level_at_end" in result.columns


def test_join_sea_level_adds_mean_sea_level_while_disaster():
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31", value=5.0)
    df = _make_flood_df("2005-06-01", "2005-06-10")
    result = join_sea_level(df, sea)
    assert "mean_sea_level_while_disaster" in result.columns
    assert result["mean_sea_level_while_disaster"].iloc[0] == pytest.approx(5.0)


def test_join_sea_level_adds_sea_trend_at_start():
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31")
    df = _make_flood_df("2005-06-01", "2005-06-05")
    result = join_sea_level(df, sea)
    assert "sea_trend_at_start" in result.columns


def test_join_sea_level_nan_when_start_not_in_sea_level():
    sea = _make_daily_sea_level("2005-01-01", "2005-06-01")
    df = _make_flood_df("2006-01-01", "2006-01-10")
    result = join_sea_level(df, sea)
    assert pd.isna(result["sea_level_at_start"].iloc[0])


def test_join_sea_level_returns_copy():
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31")
    df = _make_flood_df("2005-06-01", "2005-06-05")
    result = join_sea_level(df, sea)
    result["sea_level_at_start"] = 999
    assert "sea_level_at_start" not in df.columns


# ── drop_join_redundant_cols ──────────────────────────────────────────────────


def _make_df_with_redundant_cols() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DisNo.": ["A"],
            "Disaster Type": ["Flood"],
            "Disaster Subgroup": ["Hydrological"],
            "Start Year": [2005],
            "Start Month": [6],
            "Start Day": [1],
            "End Year": [2005],
            "End Month": [6],
            "End Day": [10],
            "Country": ["Italy"],
        }
    )


def test_drop_join_redundant_cols_removes_expected_columns():
    df = _make_df_with_redundant_cols()
    result = drop_join_redundant_cols(df)
    for col in [
        "Disaster Type",
        "Disaster Subgroup",
        "Start Year",
        "Start Month",
        "Start Day",
        "End Year",
        "End Month",
        "End Day",
    ]:
        assert col not in result.columns


def test_drop_join_redundant_cols_keeps_remaining_columns():
    df = _make_df_with_redundant_cols()
    result = drop_join_redundant_cols(df)
    assert "DisNo." in result.columns
    assert "Country" in result.columns


def test_drop_join_redundant_cols_resets_index():
    df = _make_df_with_redundant_cols()
    df.index = [42]
    result = drop_join_redundant_cols(df)
    assert list(result.index) == [0]


def test_drop_join_redundant_cols_custom_cols():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    result = drop_join_redundant_cols(df, cols=["b"])
    assert "b" not in result.columns
    assert "a" in result.columns
