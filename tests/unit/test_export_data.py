from __future__ import annotations

import pandas as pd
import pytest

from myproj.io import export_data


@pytest.fixture
def processed_dir(tmp_path, monkeypatch):
    proc_dir = tmp_path / "data" / "processed"
    monkeypatch.setattr(export_data, "PROCESSED_DIR", proc_dir)
    return proc_dir


def test_save_processed_data_creates_parquet_file(processed_dir):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    export_data.save_processed_data(df, "test.parquet")
    assert (processed_dir / "test.parquet").exists()


def test_save_processed_data_creates_directory_if_missing(tmp_path, monkeypatch):
    missing_dir = tmp_path / "does" / "not" / "exist"
    monkeypatch.setattr(export_data, "PROCESSED_DIR", missing_dir)
    df = pd.DataFrame({"x": [1]})
    export_data.save_processed_data(df, "out.parquet")
    assert (missing_dir / "out.parquet").exists()


def test_save_processed_data_returns_correct_path(processed_dir):
    df = pd.DataFrame({"a": [1]})
    path = export_data.save_processed_data(df, "result.parquet")
    assert path == processed_dir / "result.parquet"


def test_save_processed_data_content_is_readable(processed_dir):
    df = pd.DataFrame({"col": [10, 20, 30]})
    export_data.save_processed_data(df, "data.parquet")
    loaded = pd.read_parquet(processed_dir / "data.parquet")
    assert list(loaded["col"]) == [10, 20, 30]


def test_save_processed_data_does_not_write_index(processed_dir):
    df = pd.DataFrame({"val": [1, 2]}, index=[10, 20])
    export_data.save_processed_data(df, "no_index.parquet")
    loaded = pd.read_parquet(processed_dir / "no_index.parquet")
    assert list(loaded.index) == [0, 1]
