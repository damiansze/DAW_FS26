from __future__ import annotations

import logging

import pandas as pd

from myproj._utils import fmt_ids

logger = logging.getLogger("myproj.cleaning")


def drop_duplicates(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Entfernt Zeilen mit doppeltem id_col (keep='first') und loggt die entfernten IDs."""
    dup_mask = df.duplicated(subset=[id_col], keep="first")
    n = int(dup_mask.sum())
    if n > 0:
        ids = df.loc[dup_mask, id_col].astype(str).tolist()
        logger.info("drop_duplicates | id_col: %s | removed: %d | ids: %s", id_col, n, fmt_ids(ids))
    else:
        logger.info("drop_duplicates | id_col: %s | removed: 0", id_col)
    return df[~dup_mask].copy()


def drop_impossible_dates(
    df: pd.DataFrame,
    start_col: str = "Start Year",
    end_col: str = "End Year",
    id_col: str = "DisNo.",
) -> pd.DataFrame:
    """Entfernt Zeilen, bei denen End Year < Start Year (logisch unmöglich)."""
    end = pd.to_numeric(df[end_col], errors="coerce")
    start = pd.to_numeric(df[start_col], errors="coerce")
    mask = end.notna() & start.notna() & (end < start)
    n = int(mask.sum())
    if n > 0:
        ids = df.loc[mask, id_col].astype(str).tolist()
        logger.info("drop_impossible_dates | removed: %d | ids: %s", n, fmt_ids(ids))
    else:
        logger.info("drop_impossible_dates | removed: 0")
    return df[~mask].copy()


def drop_missing_start_year(
    df: pd.DataFrame,
    year_col: str = "Start Year",
    id_col: str = "DisNo.",
) -> pd.DataFrame:
    """Entfernt Zeilen ohne Start Year (zeitlich nicht einordenbar)."""
    mask = df[year_col].isna()
    n = int(mask.sum())
    if n > 0:
        ids = df.loc[mask, id_col].astype(str).tolist()
        logger.info("drop_missing_start_year | removed: %d | ids: %s", n, fmt_ids(ids))
    else:
        logger.info("drop_missing_start_year | removed: 0")
    return df[~mask].copy()


def flag_outliers(
    df: pd.DataFrame,
    cols: list[str],
    id_col: str = "DisNo.",
) -> pd.DataFrame:
    """Flaggt Zeilen als Outlier per Spalte und kombiniert (IQR-Methode).

    Pro Spalte in *cols* wird eine neue Spalte ``is_outlier_<col>`` angelegt.
    Zusätzlich fasst ``is_outlier`` (OR über alle Spalten) zusammen, ob ein
    Eintrag in mindestens einer Spalte ausserhalb von
    [Q1 - 1.5*IQR, Q3 + 1.5*IQR] liegt.
    """
    df = df.copy()
    combined_mask = pd.Series(False, index=df.index)
    for col in cols:
        values = pd.to_numeric(df[col], errors="coerce")
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        col_mask = values.notna() & ((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr))
        df[f"is_outlier_{col}"] = col_mask
        combined_mask |= col_mask
        n_col = int(col_mask.sum())
        if n_col > 0:
            ids = df.loc[col_mask, id_col].astype(str).tolist()
            logger.info("flag_outliers | col: %s | flagged: %d | ids: %s", col, n_col, fmt_ids(ids))
        else:
            logger.info("flag_outliers | col: %s | flagged: 0", col)
    df["is_outlier"] = combined_mask
    n_total = int(combined_mask.sum())
    logger.info("flag_outliers | cols: %s | total flagged: %d", cols, n_total)
    return df


def impute_missing_measurements(
    df: pd.DataFrame,
    time_col: str = "time",
    cols: list[str] | None = None,
) -> pd.DataFrame:
    """Imputiert fehlende Messwerte per linearer Interpolation.

    Randwerte (Anfang/Ende der Reihe) werden per ffill/bfill aufgefüllt,
    da lineare Interpolation dort keinen zweiten Ankerpunkt hat.
    """
    if cols is None:
        cols = [
            "MSL_filtered_GIA_corrected_adjusted",
            "trend_MSL_filtered_GIA_corrected_adjusted",
        ]
    df = df.copy()
    for col in cols:
        mask = df[col].isna()
        n = int(mask.sum())
        if n > 0:
            timestamps = df.loc[mask, time_col].dt.strftime("%Y-%m-%d").tolist()
            df[col] = df[col].interpolate(method="linear").ffill().bfill()
            logger.info(
                "impute_missing_measurements | col: %s | imputed: %d | timestamps: %s",
                col,
                n,
                fmt_ids(timestamps),
            )
        else:
            logger.info("impute_missing_measurements | col: %s | imputed: 0", col)
    return df
