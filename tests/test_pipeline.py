from myproj.pipeline import run_import


def test_import_returns_dataframes():
    df_a, df_b = run_import()
    assert not df_a.empty
    assert not df_b.empty