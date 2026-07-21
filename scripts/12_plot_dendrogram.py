"""Plot hierarchical clustering dendrograms from averaged DockQ scores."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

from _cli_helpers import prompt_path


def build_distance_matrix(average_dockq: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    split_pairs = average_dockq["key"].str.split("-", expand=True)
    average_dockq = average_dockq.assign(Model_PDB1=split_pairs[0], Model_PDB2=split_pairs[1])
    unique_models = pd.unique(average_dockq[["Model_PDB1", "Model_PDB2"]].values.ravel("K"))
    model_to_index = {model: idx for idx, model in enumerate(unique_models)}
    distance_matrix = np.ones((len(unique_models), len(unique_models)))
    np.fill_diagonal(distance_matrix, 0)

    for _, row in average_dockq.iterrows():
        idx1 = model_to_index[row["Model_PDB1"]]
        idx2 = model_to_index[row["Model_PDB2"]]
        distance = 1 - row["Average_DockQ"]
        distance_matrix[idx1, idx2] = distance
        distance_matrix[idx2, idx1] = distance

    return distance_matrix, list(unique_models)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, nargs="?", help="CSV produced by script 07.")
    parser.add_argument(
        "--full-output",
        type=Path,
        default=Path("results/clustering/dendrogram_full.png"),
        help="Output PNG for the full dendrogram.",
    )
    parser.add_argument(
        "--truncated-output",
        type=Path,
        default=Path("results/clustering/dendrogram_truncated.png"),
        help="Output PNG for the truncated dendrogram.",
    )
    parser.add_argument("--truncate-p", type=int, default=50, help="Number of merged clusters to show in the truncated plot.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.input_csv = prompt_path(
        "Enter the averaged DockQ CSV path",
        args.input_csv,
        must_exist=True,
        expect_dir=False,
    )
    args.full_output.parent.mkdir(parents=True, exist_ok=True)
    args.truncated_output.parent.mkdir(parents=True, exist_ok=True)

    average_dockq = pd.read_csv(args.input_csv)
    distance_matrix, unique_models = build_distance_matrix(average_dockq)
    linkage_matrix = linkage(squareform(distance_matrix), method="average")

    plt.figure(figsize=(20, 10))
    dendrogram(
        linkage_matrix,
        labels=unique_models,
        orientation="top",
        leaf_rotation=90.0,
        leaf_font_size=8.0,
    )
    plt.title("Hierarchical Clustering Dendrogram (Average DockQ Scores)")
    plt.xlabel("Model PDB")
    plt.ylabel("Distance")
    plt.tight_layout()
    plt.savefig(args.full_output, dpi=300)

    plt.figure(figsize=(20, 10))
    dendrogram(
        linkage_matrix,
        truncate_mode="lastp",
        p=args.truncate_p,
        show_leaf_counts=False,
        leaf_rotation=90.0,
        leaf_font_size=12.0,
        show_contracted=True,
    )
    plt.title("Hierarchical Clustering Dendrogram (Truncated)")
    plt.xlabel("Merged Cluster Identifier")
    plt.ylabel("Distance")
    plt.tight_layout()
    plt.savefig(args.truncated_output, dpi=300)

    print(f"Wrote dendrogram plots to {args.full_output} and {args.truncated_output}")


if __name__ == "__main__":
    main()
