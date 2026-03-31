import pandas as pd
import pytest
import xarray as xr
from pandas.testing import assert_frame_equal
from xarray.testing import assert_identical

from myproj.io import import_data


@pytest.fixture
def raw_data_dir(tmp_path, monkeypatch):
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    monkeypatch.setattr(import_data, "DATA_RAW", raw_dir)
    return raw_dir


def test_find_project_root_returns_nearest_parent_with_pyproject(tmp_path, monkeypatch):
    outer_root = tmp_path / "outer"
    project_root = outer_root / "project"
    working_dir = project_root / "src" / "myproj"

    outer_root.mkdir()
    project_root.mkdir()
    working_dir.mkdir(parents=True)

    (outer_root / "pyproject.toml").write_text("[project]\nname='outer'\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        "[project]\nname='project'\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(working_dir)

    assert import_data.find_project_root() == project_root.resolve()


def test_find_project_root_raises_when_no_pyproject_exists(tmp_path, monkeypatch):
    working_dir = tmp_path / "nested" / "folder"
    working_dir.mkdir(parents=True)
    monkeypatch.chdir(working_dir)

    with pytest.raises(FileNotFoundError, match="Projektroot nicht gefunden"):
        import_data.find_project_root()


def test_get_raw_file_path_returns_existing_file(raw_data_dir):
    data_file = raw_data_dir / "input.xlsx"
    data_file.write_text("placeholder", encoding="utf-8")

    assert import_data.get_raw_file_path("input.xlsx") == data_file


def test_get_raw_file_path_raises_for_missing_file(raw_data_dir):
    missing_file = raw_data_dir / "missing.xlsx"

    with pytest.raises(FileNotFoundError, match=str(missing_file)):
        import_data.get_raw_file_path("missing.xlsx")


def test_load_raw_data_reads_excel_file(raw_data_dir):
    expected = pd.DataFrame({"year": [2020, 2021], "value": [1.5, 2.0]})
    excel_file = raw_data_dir / "sample.xlsx"
    expected.to_excel(excel_file, index=False)

    result = import_data.load_raw_data("sample.xlsx")

    assert_frame_equal(result, expected)


def test_load_raw_data_reads_netcdf_file(raw_data_dir):
    expected = xr.Dataset({"temperature": ("time", [12.1, 13.4])}, coords={"time": [0, 1]})
    dataset_file = raw_data_dir / "sample.nc"
    expected.to_netcdf(dataset_file, engine="h5netcdf")

    result = import_data.load_raw_data("sample.nc")

    try:
        assert_identical(result, expected)
    finally:
        result.close()


def test_load_raw_data_raises_for_unsupported_file_type(raw_data_dir):
    unsupported_file = raw_data_dir / "sample.txt"
    unsupported_file.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Nicht unterstütztes Dateiformat: \\.txt"):
        import_data.load_raw_data("sample.txt")
