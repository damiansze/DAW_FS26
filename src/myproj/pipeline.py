from __future__ import annotations

import logging

import pandas as pd

from myproj.cleaning.clean import (
    drop_duplicates,
    drop_impossible_dates,
    drop_missing_start_year,
    impute_missing_measurements,
)
from myproj.io.export_data import save_processed_data
from myproj.io.import_data import load_raw_data
from myproj.link.join import drop_join_redundant_cols, join_sea_level, prepare_sea_level_ts
from myproj.transform.filter import (
    filter_to_floods,
    filter_to_mediterranean,
    filter_to_sea_level_coverage,
    select_columns,
)
from myproj.transform.transform import (
    add_derived_columns,
    add_event_dates,
    add_sea_level_lags,
    add_sea_level_z_scores,
)

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
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(name)s | %(message)s", force=True
    )


def run_import() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_import | start")
    emdat_raw = load_raw_data(EMDAT_FILE)
    climate_raw = load_raw_data(SEA_LEVEL_FILE)
    sea_level_raw = climate_raw.to_dataframe().reset_index()
    climate_raw.close()
    logger.info("run_import | done")
    return emdat_raw, sea_level_raw


def run_pre_filter(
    emdat_raw: pd.DataFrame,
    sea_level_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_pre_filter | start")
    emdat = select_columns(emdat_raw, EMDAT_KEEP_COLS)
    emdat = filter_to_sea_level_coverage(emdat, sea_level_raw)
    sea_level = select_columns(sea_level_raw, SEA_LEVEL_KEEP_COLS)
    logger.info("run_pre_filter | done")
    return emdat, sea_level


def run_cleaning(
    emdat: pd.DataFrame,
    sea_level: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("run_cleaning | start")
    emdat = drop_duplicates(emdat, id_col="DisNo.")
    emdat = drop_impossible_dates(emdat)
    emdat = drop_missing_start_year(emdat)
    sea_level = drop_duplicates(sea_level, id_col="time")
    sea_level = impute_missing_measurements(sea_level)
    logger.info("run_cleaning | done")
    return emdat, sea_level


def run_post_filter(emdat: pd.DataFrame) -> pd.DataFrame:
    logger.info("run_post_filter | start")
    emdat_flood = filter_to_floods(emdat)
    emdat_flood = filter_to_mediterranean(emdat_flood)
    logger.info("run_post_filter | done")
    return emdat_flood


def run_transform(emdat_flood: pd.DataFrame) -> pd.DataFrame:
    logger.info("run_transform | start")
    emdat_flood = add_event_dates(emdat_flood)
    emdat_flood = add_derived_columns(emdat_flood)
    logger.info("run_transform | done")
    return emdat_flood


def run_join(emdat_flood: pd.DataFrame, sea_level: pd.DataFrame) -> pd.DataFrame:
    logger.info("run_join | start")
    sea_level_ts = prepare_sea_level_ts(sea_level)
    flood_linked = join_sea_level(emdat_flood, sea_level_ts)
    flood_linked = add_sea_level_lags(flood_linked, sea_level_ts)
    flood_linked = add_sea_level_z_scores(flood_linked, sea_level_ts)
    flood_linked = drop_join_redundant_cols(flood_linked)
    logger.info("run_join | done")
    return flood_linked


def run_export(flood_linked: pd.DataFrame) -> None:
    logger.info("run_export | start")
    save_processed_data(flood_linked, "flood_linked.parquet")
    logger.info("run_export | done")


def main() -> None:
    configure_logging()
    logger.info("Pipeline gestartet")
    emdat_raw, sea_level_raw = run_import()
    emdat, sea_level = run_pre_filter(emdat_raw, sea_level_raw)
    emdat, sea_level = run_cleaning(emdat, sea_level)
    emdat_flood = run_post_filter(emdat)
    emdat_flood = run_transform(emdat_flood)
    flood_linked = run_join(emdat_flood, sea_level)
    run_export(flood_linked)


if __name__ == "__main__":
    main()
