from __future__ import annotations

import pandas as pd

from myproj.config import ensure_dirs, output_path


def run_import() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Import raw data sources (placeholder)."""
    df_a = pd.DataFrame({"id": [1, 2, 3]})
    df_b = pd.DataFrame({"id": [1, 2, 4]})
    return df_a, df_b


def run_all() -> None:
    ensure_dirs()

    df_a, df_b = run_import()

    df_a.to_parquet(output_path(), index=False)
    print(f"Saved to {output_path()}")


def main() -> None:
    run_all()


if __name__ == "__main__":
    main()