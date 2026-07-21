"""Replace model names with legend codes in a combined score table."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legend_excel", type=Path, help="Excel workbook containing a 'Legend' sheet.")
    parser.add_argument("input_csv", type=Path, help="Combined score table to recode.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/tables/coded1_all_data_combined.csv"),
        help="Output CSV with model names replaced by codes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    legend_df = pd.read_excel(args.legend_excel, sheet_name="Legend", engine="openpyxl")
    legend_dict = dict(zip(legend_df["Model"], legend_df["Code"]))
    data_df = pd.read_csv(args.input_csv)

    for column in ["Model1", "Model2"]:
        data_df[column] = data_df[column].map(lambda value: legend_dict.get(value, value))

    drop_columns = [column for column in ["Cluster1", "Cluster2"] if column in data_df.columns]
    if drop_columns:
        data_df = data_df.drop(columns=drop_columns)

    data_df.to_csv(args.output, index=False)
    print(f"Wrote coded table to {args.output}")


if __name__ == "__main__":
    main()
