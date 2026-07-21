"""Merge self-score and cross-score workbooks into a single CSV table."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def normalize_sheet_name(name: str) -> str:
    name = re.sub(r"_self_scores$", "", name)
    name = re.sub(r"_p\d+$", "", name)
    return name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("self_workbook", type=Path, help="Workbook generated from self-comparison scores.")
    parser.add_argument("cross_workbook", type=Path, help="Workbook generated from cross-comparison scores.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/tables/all_data_combined.csv"),
        help="Output CSV containing merged score rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    self_xl = pd.ExcelFile(args.self_workbook, engine="openpyxl")
    cross_xl = pd.ExcelFile(args.cross_workbook, engine="openpyxl")

    cross_lookup: dict[str, list[str]] = {}
    for sheet_name in cross_xl.sheet_names:
        cross_lookup.setdefault(normalize_sheet_name(sheet_name), []).append(sheet_name)

    merged_frames: list[pd.DataFrame] = []
    unmatched_sheets: list[str] = []

    for self_sheet_name in self_xl.sheet_names:
        normalized = normalize_sheet_name(self_sheet_name)
        matching_cross_sheets = cross_lookup.get(normalized, [])
        if not matching_cross_sheets:
            unmatched_sheets.append(self_sheet_name)
            continue

        combined_df = self_xl.parse(self_sheet_name)
        for cross_sheet_name in matching_cross_sheets:
            cross_df = cross_xl.parse(cross_sheet_name)
            combined_df = pd.concat([combined_df, cross_df], ignore_index=True)
            print(f"Merged {self_sheet_name} with {cross_sheet_name}")

        merged_frames.append(combined_df)

    if not merged_frames:
        raise SystemExit("No matching sheets were found between the two workbooks.")

    final_df = pd.concat(merged_frames, ignore_index=True)
    final_df.to_csv(args.output, index=False)
    print(f"Wrote merged CSV to {args.output}")

    if unmatched_sheets:
        print("Unmatched self-score sheets:")
        for sheet in unmatched_sheets:
            print(f"  - {sheet}")


if __name__ == "__main__":
    main()
