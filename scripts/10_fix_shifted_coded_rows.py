"""Shift non-empty row values left in a CSV table."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def shift_row_left(row: pd.Series) -> list[object]:
    non_nans = row.dropna().tolist()
    nans_to_append = [np.nan] * (len(row) - len(non_nans))
    return non_nans + nans_to_append


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, help="Input CSV whose rows may be offset.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path. Defaults to FIXED_<input name> in the same directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output or args.input_csv.with_name(f"FIXED_{args.input_csv.name}")

    data_df = pd.read_csv(args.input_csv)
    corrected_rows = [shift_row_left(row) for _, row in data_df.iterrows()]
    corrected_df = pd.DataFrame(corrected_rows, columns=data_df.columns)
    corrected_df.to_csv(output_path, index=False)

    print(f"Wrote shifted table to {output_path}")


if __name__ == "__main__":
    main()
