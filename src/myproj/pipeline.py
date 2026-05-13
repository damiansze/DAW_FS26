from __future__ import annotations

import logging

import pandas as pd

from myproj.cleaning.clean import (
    drop_duplicates,
    drop_impossible_dates,
    drop_missing_start_year,
    flag_outliers,
    impute_missing_measurements,
)
from myproj.io.import_data import load_raw_data
from myproj.transform.trim_data import filter_to_sea_level_coverage, select_columns

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("myproj.pipeline")

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


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=format, force=True)


def run_import() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_import | start")
    emdat_raw = load_raw_data(EMDAT_FILE)
    climate_raw = load_raw_data(SEA_LEVEL_FILE)
    sea_level_raw = climate_raw.to_dataframe().reset_index()
    climate_raw.close()
    logger.info("run_import | done")
    return emdat_raw, sea_level_raw


def run_transform(
    emdat_raw: pd.DataFrame,
    sea_level_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_transform | start")
    emdat = select_columns(emdat_raw, EMDAT_KEEP_COLS)
    emdat = filter_to_sea_level_coverage(emdat, sea_level_raw)
    sea_level = select_columns(sea_level_raw, SEA_LEVEL_KEEP_COLS)
    logger.info("run_transform | done")
    return emdat, sea_level


def run_cleaning(
    emdat: pd.DataFrame,
    sea_level: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_cleaning | start")
    emdat = drop_duplicates(emdat, id_col="DisNo.")
    emdat = drop_impossible_dates(emdat)
    emdat = drop_missing_start_year(emdat)
    emdat = flag_outliers(emdat, cols=["Total Affected", "Total Deaths"])
    sea_level = drop_duplicates(sea_level, id_col="time")
    sea_level = impute_missing_measurements(sea_level)
    logger.info("run_cleaning | done")
    return emdat, sea_level


def main() -> None:
    configure_logging()
    logger.info("Pipeline gestartet")
    emdat_raw, sea_level_raw = run_import()
    emdat, sea_level = run_transform(emdat_raw, sea_level_raw)
    emdat, sea_level = run_cleaning(emdat, sea_level)
    # run_prepare(), run_join(), run_save() folgen


if __name__ == "__main__":
    main()
