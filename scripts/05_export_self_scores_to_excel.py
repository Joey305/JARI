"""Export self-comparison DockQ text reports into a multi-sheet Excel workbook."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd


def get_excel_engine() -> str:
    return "xlsxwriter" if importlib.util.find_spec("xlsxwriter") else "openpyxl"


def normalize_sheet_base_name(filename: str) -> str:
    return filename.replace("_self_scores", "")


def write_to_excel(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str) -> None:
    max_rows = 1_048_576
    if df.shape[0] > max_rows:
        for index, start_row in enumerate(range(0, df.shape[0], max_rows), start=1):
            df_chunk = df.iloc[start_row:start_row + max_rows, :]
            chunk_sheet_name = f"{sheet_name[:24]}_part{index}"
            df_chunk.to_excel(writer, sheet_name=chunk_sheet_name[:31], index=False)
    else:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)


def parse_model_names(filename: str) -> tuple[str, str]:
    model_name = filename.replace("_self_scores", "")
    return model_name, model_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("txt_folder", type=Path, help="Directory containing self-comparison DockQ .txt files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/workbooks/self_scores.xlsx"),
        help="Output Excel workbook path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    txt_files = sorted(args.txt_folder.glob("*.txt"))

    if not txt_files:
        raise SystemExit(f"No .txt files found in {args.txt_folder}")

    with pd.ExcelWriter(args.output, engine=get_excel_engine()) as writer:
        for txt_file in txt_files:
            df = pd.read_csv(txt_file, delimiter="\t")
            model1, model2 = parse_model_names(txt_file.stem)
            df["Model1"] = model1
            df["Model2"] = model2
            write_to_excel(df, writer, normalize_sheet_base_name(txt_file.stem)[:31])
            print(f"Processed {txt_file.name}")

    print(f"Wrote workbook to {args.output}")


if __name__ == "__main__":
    main()
