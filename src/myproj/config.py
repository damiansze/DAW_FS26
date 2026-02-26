from __future__ import annotations

from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = "example.parquet"


def ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def output_path() -> Path:
    return PROCESSED_DIR / OUTPUT_FILE
