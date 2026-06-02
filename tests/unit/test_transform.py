from __future__ import annotations

import pandas as pd
import pytest

from myproj.transform.transform import (
    add_derived_columns,
    add_event_dates,
    add_sea_level_lags,
    add_sea_level_z_scores,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_emdat(**kwargs) -> pd.DataFrame:
    defaults = {
        "Start Year": [2005],
        "Start Month": [6],
        "Start Day": [1],
        "End Year": [2005],
        "End Month": [6],
        "End Day": [10],
        "Latitude": [41.0],
        "Longitude": [12.0],
    }
    defaults.update(kwargs)
    return pd.DataFrame(defaults)


def _make_sea_level(values: list[float], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.to_datetime(dates),
            "MSL_filtered_GIA_corrected_adjusted": values,
            "trend_MSL_filtered_GIA_corrected_adjusted": values,
        }
    )


# ── add_event_dates ───────────────────────────────────────────────────────────


def test_add_event_dates_creates_start_and_end_date_columns():
    df = _make_emdat()
    result = add_event_dates(df)
    assert "start_date" in result.columns
    assert "end_date" in result.columns


def test_add_event_dates_correct_start_date():
    df = _make_emdat(**{"Start Year": [2005], "Start Month": [3], "Start Day": [15]})
    result = add_event_dates(df)
    assert result["start_date"].iloc[0] == pd.Timestamp("2005-03-15")


def test_add_event_dates_imputes_missing_month_to_january():
    df = _make_emdat(**{"Start Year": [2005], "Start Month": [None], "Start Day": [None]})
    result = add_event_dates(df)
    assert result["start_date"].iloc[0] == pd.Timestamp("2005-01-01")


def test_add_event_dates_adds_quality_columns():
    df = _make_emdat()
    result = add_event_dates(df)
    assert "start_date_quality" in result.columns
    assert "end_date_quality" in result.columns


def test_add_event_dates_quality_complete_when_all_present():
    df = _make_emdat()
    result = add_event_dates(df)
    assert result["start_date_quality"].iloc[0] == "complete"


def test_add_event_dates_quality_flags_missing_day():
    df = _make_emdat(**{"Start Year": [2005], "Start Month": [6], "Start Day": [None]})
    result = add_event_dates(df)
    assert result["start_date_quality"].iloc[0] == "day_imputed"


def test_add_event_dates_quality_flags_missing_month_and_day():
    df = _make_emdat(**{"Start Year": [2005], "Start Month": [None], "Start Day": [None]})
    result = add_event_dates(df)
    assert result["start_date_quality"].iloc[0] == "month_and_day_imputed"


def test_add_event_dates_returns_copy():
    df = _make_emdat()
    result = add_event_dates(df)
    result["start_date"] = pd.NaT
    assert "start_date" not in df.columns


# ── add_derived_columns ───────────────────────────────────────────────────────


def _make_emdat_with_dates() -> pd.DataFrame:
    df = _make_emdat()
    return add_event_dates(df)


def test_add_derived_columns_adds_season():
    df = _make_emdat_with_dates()
    result = add_derived_columns(df)
    assert "season" in result.columns


def test_add_derived_columns_summer_for_june():
    df = _make_emdat(**{"Start Month": [7]})
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["season"].iloc[0] == "summer"


def test_add_derived_columns_winter_for_december():
    df = _make_emdat(**{"Start Month": [12]})
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["season"].iloc[0] == "winter"


def test_add_derived_columns_unknown_season_when_month_missing():
    df = _make_emdat(**{"Start Month": [None]})
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["season"].iloc[0] == "unknown"


def test_add_derived_columns_adds_event_duration_days():
    df = _make_emdat(
        **{
            "Start Year": [2005],
            "Start Month": [6],
            "Start Day": [1],
            "End Year": [2005],
            "End Month": [6],
            "End Day": [5],
        }
    )
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["event_duration_days"].iloc[0] == 5


def test_add_derived_columns_duration_minimum_is_one():
    df = _make_emdat(
        **{
            "Start Year": [2005],
            "Start Month": [6],
            "Start Day": [1],
            "End Year": [2005],
            "End Month": [6],
            "End Day": [1],
        }
    )
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["event_duration_days"].iloc[0] == 1


def test_add_derived_columns_adds_has_coordinates():
    df = _make_emdat_with_dates()
    result = add_derived_columns(df)
    assert "has_coordinates" in result.columns
    assert result["has_coordinates"].iloc[0] is True or result["has_coordinates"].iloc[0] == True  # noqa: E712


def test_add_derived_columns_has_coordinates_false_when_missing():
    df = _make_emdat(**{"Latitude": [None], "Longitude": [None]})
    df = add_event_dates(df)
    result = add_derived_columns(df)
    assert result["has_coordinates"].iloc[0] == False  # noqa: E712


def test_add_derived_columns_returns_copy():
    df = _make_emdat_with_dates()
    result = add_derived_columns(df)
    result["season"] = "x"
    assert "season" not in df.columns


# ── add_sea_level_lags ────────────────────────────────────────────────────────


def _make_flood_df_with_start(start: str) -> pd.DataFrame:
    return pd.DataFrame({"start_date": pd.to_datetime([start])})


def _make_daily_sea_level(start: str, end: str, value: float = 10.0) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame(
        {
            "time": dates,
            "MSL_filtered_GIA_corrected_adjusted": [value] * len(dates),
        }
    )


def test_add_sea_level_lags_adds_n_lag_columns():
    df = _make_flood_df_with_start("2005-06-10")
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31")
    result = add_sea_level_lags(df, sea, n_lags=3)
    assert "sea_level_lag_1d" in result.columns
    assert "sea_level_lag_2d" in result.columns
    assert "sea_level_lag_3d" in result.columns


def test_add_sea_level_lags_default_five_lags():
    df = _make_flood_df_with_start("2005-06-10")
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31")
    result = add_sea_level_lags(df, sea)
    assert all(f"sea_level_lag_{n}d" in result.columns for n in range(1, 6))


def test_add_sea_level_lags_correct_lag_value():
    df = _make_flood_df_with_start("2005-06-10")
    dates = pd.date_range("2005-01-01", "2005-12-31", freq="D")
    values = list(range(len(dates)))
    sea = pd.DataFrame({"time": dates, "MSL_filtered_GIA_corrected_adjusted": values})
    result = add_sea_level_lags(df, sea, n_lags=1)
    start_idx = dates.get_loc(pd.Timestamp("2005-06-10"))
    assert result["sea_level_lag_1d"].iloc[0] == values[start_idx - 1]


def test_add_sea_level_lags_returns_copy():
    df = _make_flood_df_with_start("2005-06-10")
    sea = _make_daily_sea_level("2005-01-01", "2005-12-31")
    result = add_sea_level_lags(df, sea, n_lags=1)
    result["sea_level_lag_1d"] = 999
    assert "sea_level_lag_1d" not in df.columns


# ── add_sea_level_z_scores ────────────────────────────────────────────────────


def _make_joined_df(sea_at_start: float, mean_sea: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sea_level_at_start": [sea_at_start],
            "mean_sea_level_while_disaster": [mean_sea],
        }
    )


def test_add_sea_level_z_scores_adds_z_score_columns():
    df = _make_joined_df(10.0, 12.0)
    sea = _make_sea_level(
        [8.0, 10.0, 12.0, 14.0, 16.0],
        ["2005-01-01", "2005-01-02", "2005-01-03", "2005-01-04", "2005-01-05"],
    )
    result = add_sea_level_z_scores(df, sea)
    assert "sea_level_at_start_z" in result.columns
    assert "mean_sea_level_while_disaster_z" in result.columns


def test_add_sea_level_z_scores_mean_value_has_z_score_zero():
    # A value equal to the mean gets z-score 0
    values = [8.0, 10.0, 12.0, 14.0, 16.0]
    mean = sum(values) / len(values)  # 12.0
    df = _make_joined_df(sea_at_start=mean, mean_sea=mean)
    sea = _make_sea_level(
        values, ["2005-01-01", "2005-01-02", "2005-01-03", "2005-01-04", "2005-01-05"]
    )
    result = add_sea_level_z_scores(df, sea)
    assert result["sea_level_at_start_z"].iloc[0] == pytest.approx(0.0)


def test_add_sea_level_z_scores_returns_copy():
    df = _make_joined_df(10.0, 12.0)
    sea = _make_sea_level([8.0, 10.0, 12.0], ["2005-01-01", "2005-01-02", "2005-01-03"])
    result = add_sea_level_z_scores(df, sea)
    result["sea_level_at_start_z"] = 999
    assert "sea_level_at_start_z" not in df.columns
