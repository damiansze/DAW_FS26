from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger("myproj.transform")


def select_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Nur angegebene Spalten behalten. Raises ValueError bei fehlenden Spalten."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        logger.error("Spaltenauswahl fehlgeschlagen; fehlende Spalten: %s", missing)
        raise ValueError(f"Spalten nicht vorhanden im DataFrame: {missing}")
    result = df[columns].copy()
    logger.info(
        "select_columns | cols: %d → %d",
        len(df.columns),
        len(columns),
    )
    return result


def filter_before_sea_level_start(
    df: pd.DataFrame,
    year_col: str = "Start Year",
    month_col: str = "Start Month",
    day_col: str = "Start Day",
) -> pd.DataFrame:
    """
    Entfernt EMDAT-Einträge, die eindeutig vor 1999-02-20 liegen
    (erster Sea-Level-Messwert).

    Nur Einträge die klar vor dem Cutoff einzuordnen sind werden entfernt:
      - Start Year < 1999
      - Start Year = 1999 AND Start Month = 1
      - Start Year = 1999 AND Start Month = 2 AND Start Day bekannt AND < 20

    Einträge mit fehlendem Monat oder Tag in 1999 werden behalten.
    """
    year = df[year_col]
    month = df[month_col]
    day = df[day_col]

    remove = (
        (year < 1999)
        | ((year == 1999) & (month == 1))
        | ((year == 1999) & (month == 2) & day.notna() & (day < 20))
    )
    result = df[~remove].copy()
    logger.info(
        "filter_before_sea_level_start | rows: %d → %d | removed: %d",
        len(df),
        len(result),
        len(df) - len(result),
    )
    return result
