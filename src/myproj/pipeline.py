from __future__ import annotations

import pandas as pd

from myproj.io.import_data import load_raw_data
from myproj.transform.trim_data import filter_before_sea_level_start, select_columns

# ── Dateinamen ────────────────────────────────────────────────────────────────

EMDAT_FILE = "public_emdat_1991_2024.xlsx"
SEA_LEVEL_FILE = "omi_climate_sl_medsea_area_averaged_anomalies_19990220_P20250729.nc"

# ── Spaltenauswahl ────────────────────────────────────────────────────────────

EMDAT_KEEP_COLS = [
    "DisNo.",
    "ISO",
    "Country",
    "Region",
    "Disaster Subgroup",
    "Disaster Type",
    "Disaster Subtype",
    "Origin",
    "Start Year",
    "Start Month",
    "Start Day",
    "End Year",
    "End Month",
    "End Day",
    "Latitude",
    "Longitude",
    "Total Affected",
    "Total Deaths",
]

SEA_LEVEL_KEEP_COLS = [
    "time",
    "MSL_filtered_GIA_corrected_adjusted",
    "trend_MSL_filtered_GIA_corrected_adjusted",
]

# ── Pipeline-Schritte ─────────────────────────────────────────────────────────


def run_import() -> tuple[pd.DataFrame, pd.DataFrame]:
    emdat_raw = load_raw_data(EMDAT_FILE)
    climate_raw = load_raw_data(SEA_LEVEL_FILE)
    sea_level_raw = climate_raw.to_dataframe().reset_index()
    climate_raw.close()
    return emdat_raw, sea_level_raw


def run_transform(
    emdat_raw: pd.DataFrame,
    sea_level_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    emdat = select_columns(emdat_raw, EMDAT_KEEP_COLS)
    emdat = filter_before_sea_level_start(emdat)
    sea_level = select_columns(sea_level_raw, SEA_LEVEL_KEEP_COLS)
    return emdat, sea_level


def main() -> None:
    emdat_raw, sea_level_raw = run_import()
    emdat, sea_level = run_transform(emdat_raw, sea_level_raw)
    # run_cleaning(), run_prepare(), run_join(), run_save() folgen


if __name__ == "__main__":
    main()
