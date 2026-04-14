from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import xarray as xr

logger = logging.getLogger("myproj.io")


def find_project_root() -> Path:
    """
    Findet den Projektroot, indem vom aktuellen Arbeitsverzeichnis
    nach oben gesucht wird, bis eine pyproject.toml gefunden wird.
    """
    current = Path.cwd().resolve()

    for path in [current, *current.parents]:
        if (path / "pyproject.toml").exists():
            return path

    raise FileNotFoundError(
        "Projektroot nicht gefunden. Stelle sicher, dass du im Projekt "
        "oder in einem Unterordner des Projekts arbeitest."
    )


PROJECT_ROOT = find_project_root()
DATA_RAW = PROJECT_ROOT / "data" / "raw"


def get_raw_file_path(filename: str) -> Path:
    """
    Gibt den vollständigen Pfad zu einer Datei im data/raw-Ordner zurück.
    """
    file_path = DATA_RAW / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

    return file_path


def load_raw_data(filename: str):
    """
    Lädt eine Datei aus data/raw abhängig von ihrer Dateiendung.

    Unterstützte Formate:
    - .xlsx, .xls -> pandas DataFrame
    - .nc -> xarray Dataset
    """
    file_path = get_raw_file_path(filename)
    suffix = file_path.suffix.lower()

    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
        logger.info(
            "load_raw_data | file: %s | rows: %d | cols: %d",
            filename,
            len(df),
            len(df.columns),
        )
        return df

    if suffix == ".nc":
        ds = xr.open_dataset(file_path, engine="h5netcdf")
        logger.info(
            "load_raw_data | file: %s | variables: %d | dimensions: %s",
            filename,
            len(ds.data_vars),
            dict(ds.sizes),
        )
        return ds

    raise ValueError(
        f"Nicht unterstütztes Dateiformat: {suffix}. Unterstützt werden .xlsx, .xls, .nc"
    )
