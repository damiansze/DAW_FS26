from __future__ import annotations

import pandas as pd
import pytest

from myproj.cleaning.clean import (
    drop_duplicates,
    drop_impossible_dates,
    drop_missing_start_year,
    flag_outliers,
    impute_missing_measurements,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _emdat(rows: list[dict]) -> pd.DataFrame:
    """Minimal EMDAT DataFrame with required columns."""
    defaults = {"DisNo.": "X", "Start Year": 2000, "End Year": 2000}
    return pd.DataFrame([{**defaults, **r} for r in rows])


def _sea_level(values: list[float | None], dates: list[str]) -> pd.DataFrame:
    """Sea level DataFrame with time + one measurement column."""
    return pd.DataFrame(
        {
            "time": pd.to_datetime(dates),
            "MSL_filtered_GIA_corrected_adjusted": pd.array(values, dtype="Float32"),
            "trend_MSL_filtered_GIA_corrected_adjusted": pd.array(
                [1.0] * len(values), dtype="Float32"
            ),
        }
    )


# ── drop_duplicates ───────────────────────────────────────────────────────────


def test_drop_duplicates_removes_second_occurrence():
    df = _emdat([{"DisNo.": "A"}, {"DisNo.": "B"}, {"DisNo.": "A"}])
    result = drop_duplicates(df, id_col="DisNo.")
    assert list(result["DisNo."]) == ["A", "B"]


def test_drop_duplicates_no_duplicates_unchanged():
    df = _emdat([{"DisNo.": "A"}, {"DisNo.": "B"}])
    result = drop_duplicates(df, id_col="DisNo.")
    assert len(result) == 2


def test_drop_duplicates_returns_copy():
    df = _emdat([{"DisNo.": "A"}, {"DisNo.": "A"}])
    result = drop_duplicates(df, id_col="DisNo.")
    result["DisNo."] = "Z"
    assert df["DisNo."].iloc[0] == "A"


def test_drop_duplicates_works_on_timestamp_col():
    df = _sea_level([1.0, 2.0, 3.0], ["2000-01-01", "2000-01-02", "2000-01-01"])
    result = drop_duplicates(df, id_col="time")
    assert len(result) == 2
    assert list(result["time"]) == list(pd.to_datetime(["2000-01-01", "2000-01-02"]))


# ── drop_impossible_dates ─────────────────────────────────────────────────────


def test_drop_impossible_dates_removes_end_before_start():
    df = _emdat([{"DisNo.": "A", "Start Year": 2005, "End Year": 2004}])
    assert drop_impossible_dates(df).empty


def test_drop_impossible_dates_keeps_valid_rows():
    df = _emdat(
        [
            {"DisNo.": "A", "Start Year": 2000, "End Year": 2001},
            {"DisNo.": "B", "Start Year": 2000, "End Year": 2000},
        ]
    )
    assert len(drop_impossible_dates(df)) == 2


def test_drop_impossible_dates_keeps_row_when_end_year_missing():
    df = _emdat([{"DisNo.": "A", "Start Year": 2000, "End Year": None}])
    assert len(drop_impossible_dates(df)) == 1


def test_drop_impossible_dates_keeps_row_when_start_year_missing():
    df = _emdat([{"DisNo.": "A", "Start Year": None, "End Year": 2000}])
    assert len(drop_impossible_dates(df)) == 1


def test_drop_impossible_dates_returns_copy():
    df = _emdat([{"DisNo.": "A", "Start Year": 2000, "End Year": 2001}])
    result = drop_impossible_dates(df)
    result["DisNo."] = "Z"
    assert df["DisNo."].iloc[0] == "A"


# ── drop_missing_start_year ───────────────────────────────────────────────────


def test_drop_missing_start_year_removes_nan_rows():
    df = _emdat([{"DisNo.": "A", "Start Year": None}, {"DisNo.": "B", "Start Year": 2000}])
    result = drop_missing_start_year(df)
    assert list(result["DisNo."]) == ["B"]


def test_drop_missing_start_year_no_missing_unchanged():
    df = _emdat([{"DisNo.": "A", "Start Year": 2000}])
    assert len(drop_missing_start_year(df)) == 1


def test_drop_missing_start_year_returns_copy():
    df = _emdat([{"DisNo.": "A", "Start Year": 2000}])
    result = drop_missing_start_year(df)
    result["DisNo."] = "Z"
    assert df["DisNo."].iloc[0] == "A"


# ── impute_missing_measurements ───────────────────────────────────────────────


def test_impute_fills_interior_nan():
    df = _sea_level(
        [1.0, None, 3.0],
        ["2000-01-01", "2000-01-02", "2000-01-03"],
    )
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    assert result["MSL_filtered_GIA_corrected_adjusted"].isna().sum() == 0
    assert result["MSL_filtered_GIA_corrected_adjusted"].iloc[1] == pytest.approx(2.0)


def test_impute_fills_leading_nan_via_bfill():
    df = _sea_level(
        [None, 2.0, 3.0],
        ["2000-01-01", "2000-01-02", "2000-01-03"],
    )
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    assert result["MSL_filtered_GIA_corrected_adjusted"].isna().sum() == 0
    assert result["MSL_filtered_GIA_corrected_adjusted"].iloc[0] == pytest.approx(2.0)


def test_impute_fills_trailing_nan_via_ffill():
    df = _sea_level(
        [1.0, 2.0, None],
        ["2000-01-01", "2000-01-02", "2000-01-03"],
    )
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    assert result["MSL_filtered_GIA_corrected_adjusted"].isna().sum() == 0
    assert result["MSL_filtered_GIA_corrected_adjusted"].iloc[2] == pytest.approx(2.0)


def test_impute_no_missing_unchanged():
    df = _sea_level([1.0, 2.0, 3.0], ["2000-01-01", "2000-01-02", "2000-01-03"])
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    assert list(result["MSL_filtered_GIA_corrected_adjusted"]) == pytest.approx([1.0, 2.0, 3.0])


def test_impute_returns_copy():
    df = _sea_level([1.0, None, 3.0], ["2000-01-01", "2000-01-02", "2000-01-03"])
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    result["MSL_filtered_GIA_corrected_adjusted"] = 99.0
    assert df["MSL_filtered_GIA_corrected_adjusted"].iloc[0] == pytest.approx(1.0)


# ── flag_outliers ─────────────────────────────────────────────────────────────


def _emdat_with_values(values: list[float | None]) -> pd.DataFrame:
    """EMDAT DataFrame with a 'Total Deaths' column for outlier testing."""
    return pd.DataFrame(
        {
            "DisNo.": [f"ID-{i}" for i in range(len(values))],
            "Total Deaths": pd.array(values, dtype="Float64"),
        }
    )


def test_flag_outliers_adds_is_outlier_column():
    df = _emdat_with_values([1.0, 2.0, 3.0, 4.0, 5.0])
    result = flag_outliers(df, cols=["Total Deaths"])
    assert "is_outlier" in result.columns


def test_flag_outliers_flags_extreme_high_value():
    # Values 1-5 with an extreme outlier at 10000
    df = _emdat_with_values([1.0, 2.0, 3.0, 4.0, 5.0, 10000.0])
    result = flag_outliers(df, cols=["Total Deaths"])
    assert result["is_outlier"].iloc[-1] is True or result["is_outlier"].iloc[-1] == True  # noqa: E712
    assert result["is_outlier"].iloc[0] == False  # noqa: E712


def test_flag_outliers_no_outliers_all_false():
    df = _emdat_with_values([10.0, 11.0, 12.0, 11.5, 10.5])
    result = flag_outliers(df, cols=["Total Deaths"])
    assert result["is_outlier"].sum() == 0


def test_flag_outliers_does_not_remove_rows():
    df = _emdat_with_values([1.0, 2.0, 3.0, 10000.0])
    result = flag_outliers(df, cols=["Total Deaths"])
    assert len(result) == len(df)


def test_flag_outliers_nan_values_not_flagged():
    df = _emdat_with_values([1.0, None, 3.0])
    result = flag_outliers(df, cols=["Total Deaths"])
    assert result["is_outlier"].iloc[1] == False  # noqa: E712


def test_flag_outliers_returns_copy():
    df = _emdat_with_values([1.0, 2.0, 10000.0])
    result = flag_outliers(df, cols=["Total Deaths"])
    result["Total Deaths"] = 0.0
    assert df["Total Deaths"].iloc[0] == pytest.approx(1.0)


def test_flag_outliers_multiple_cols():
    # Build two columns each with a clear outlier in a different row.
    # Use enough normal values so IQR detects the extreme value reliably.
    base = [10.0, 11.0, 10.5, 11.5, 10.0, 11.0, 10.5]
    df = pd.DataFrame(
        {
            "DisNo.": [f"ID-{i}" for i in range(len(base) + 2)],
            "col_a": pd.array(base + [10000.0, 10.0], dtype="Float64"),
            "col_b": pd.array(base + [10.0, 10000.0], dtype="Float64"),
        }
    )
    result = flag_outliers(df, cols=["col_a", "col_b"])
    # Row 7: outlier only in col_a
    assert result["is_outlier"].iloc[7] == True  # noqa: E712
    # Row 8: outlier only in col_b
    assert result["is_outlier"].iloc[8] == True  # noqa: E712
    # Normal rows not flagged
    assert result["is_outlier"].iloc[0] == False  # noqa: E712


def test_impute_operates_on_specified_cols_only():
    df = _sea_level([1.0, None, 3.0], ["2000-01-01", "2000-01-02", "2000-01-03"])
    # Only impute MSL, leave trend untouched
    result = impute_missing_measurements(df, cols=["MSL_filtered_GIA_corrected_adjusted"])
    assert result["trend_MSL_filtered_GIA_corrected_adjusted"].isna().sum() == 0
