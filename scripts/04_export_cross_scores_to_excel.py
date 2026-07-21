"""Export cross-model DockQ text reports into a multi-sheet Excel workbook."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd

from _cli_helpers import prompt_path


def get_excel_engine() -> str:
    return "xlsxwriter" if importlib.util.find_spec("xlsxwriter") else "openpyxl"


def normalize_sheet_base_name(filename: str) -> str:
    return filename.replace("_dockq_high_scores", "")


def write_to_excel(df: pd.DataFrame, writer: pd.ExcelWriter, base_sheet_name: str) -> None:
    max_rows = 1_048_576
    if df.shape[0] > max_rows:
        num_chunks = (df.shape[0] // max_rows) + 1
        for i in range(num_chunks):
            start_row = i * max_rows
            end_row = min(start_row + max_rows, df.shape[0])
            chunk = df.iloc[start_row:end_row, :]
            sheet_name = f"{base_sheet_name[:28]}_p{i + 1}"
            chunk.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(writer, sheet_name=base_sheet_name[:31], index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("txt_folder", type=Path, nargs="?", help="Directory containing cross-model DockQ .txt files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/workbooks/cross_scores.xlsx"),
        help="Output Excel workbook path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.txt_folder = prompt_path(
        "Enter the directory containing cross-model DockQ text files",
        args.txt_folder,
        must_exist=True,
        expect_dir=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    txt_files = sorted(args.txt_folder.glob("*.txt"))

    if not txt_files:
        raise SystemExit(f"No .txt files found in {args.txt_folder}")

    with pd.ExcelWriter(args.output, engine=get_excel_engine()) as writer:
        for index, txt_file in enumerate(txt_files, start=1):
            df = pd.read_csv(txt_file, delimiter="\t")
            write_to_excel(df, writer, normalize_sheet_base_name(txt_file.stem)[:31])
            print(f"Processed {index} of {len(txt_files)}: {txt_file.name}")

    print(f"Wrote workbook to {args.output}")


if __name__ == "__main__":
    main()
