"""Map model/PDB combinations to compact PDB-coded identifiers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legend_excel", type=Path, help="Excel workbook containing a 'CODEDPDB' sheet.")
    parser.add_argument("input_csv", type=Path, help="CSV produced by script 08.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/tables/coded2_all_data_combined.csv"),
        help="Output CSV with PDB_CODED identifiers.",
    )
    return parser.parse_args()


def map_to_pdb_coded(row: pd.Series, mapping_dict: dict[tuple[str, str], str], model_col: str, pdb_file_col: str) -> str:
    return mapping_dict.get((row[model_col], row[pdb_file_col]), row[model_col])


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    codedpdb_df = pd.read_excel(args.legend_excel, sheet_name="CODEDPDB", engine="openpyxl")
    mapping_dict = dict(zip(zip(codedpdb_df["Code"], codedpdb_df["PDB File"]), codedpdb_df["PDB_CODED"]))

    all_data_df = pd.read_csv(args.input_csv)
    all_data_df["PDB_CODED1"] = all_data_df.apply(
        map_to_pdb_coded,
        axis=1,
        mapping_dict=mapping_dict,
        model_col="Model1",
        pdb_file_col="PDB File 1",
    )
    all_data_df["PDB_CODED2"] = all_data_df.apply(
        map_to_pdb_coded,
        axis=1,
        mapping_dict=mapping_dict,
        model_col="Model2",
        pdb_file_col="PDB File 2",
    )

    final_df = all_data_df[["PDB_CODED1", "PDB_CODED2", "DockQ", "iRMS", "LRMS"]]
    final_df.to_csv(args.output, index=False)
    print(f"Wrote PDB-coded table to {args.output}")


if __name__ == "__main__":
    main()
