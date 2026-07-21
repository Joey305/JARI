"""Average DockQ scores across unordered model-PDB pairs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _cli_helpers import prompt_path


def canonical_key(row: pd.Series) -> str:
    pair_a = f"{row['Model1']}_{row['PDB File 1']}"
    pair_b = f"{row['Model2']}_{row['PDB File 2']}"
    return "-".join(sorted([pair_a, pair_b]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, nargs="?", help="Combined score table from script 06.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/tables/averaged_dockq_scores.csv"),
        help="Output CSV containing averaged pairwise DockQ scores.",
    )
    parser.add_argument(
        "--unpaired-output",
        type=Path,
        default=Path("results/tables/unpaired_entries.csv"),
        help="Output CSV for rows that do not contain a usable pair key.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.input_csv = prompt_path(
        "Enter the combined score CSV path",
        args.input_csv,
        must_exist=True,
        expect_dir=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    required_columns = ["Model1", "PDB File 1", "Model2", "PDB File 2", "DockQ"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise SystemExit(f"Missing required columns: {', '.join(missing_columns)}")

    valid_pair_mask = df[required_columns[:-1]].notna().all(axis=1)
    unpaired_df = df.loc[~valid_pair_mask].copy()
    unpaired_df.to_csv(args.unpaired_output, index=False)

    paired_df = df.loc[valid_pair_mask].copy()
    paired_df[required_columns[:-1]] = paired_df[required_columns[:-1]].astype(str)
    paired_df["key"] = paired_df.apply(canonical_key, axis=1)
    average_dockq = paired_df.groupby("key", as_index=False).agg(Average_DockQ=("DockQ", "mean"))
    average_dockq.to_csv(args.output, index=False)

    print(f"Wrote averaged scores to {args.output}")
    print(f"Wrote unpaired rows to {args.unpaired_output}")


if __name__ == "__main__":
    main()
