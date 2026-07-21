"""Cluster averaged DockQ scores with DBSCAN and project them with UMAP."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import umap
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import MinMaxScaler


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


def fallback_embedding(num_points: int) -> np.ndarray:
    if num_points == 0:
        return np.empty((0, 2))
    if num_points == 1:
        return np.array([[0.5, 0.5]])
    x_coords = np.linspace(0.0, 1.0, num_points)
    y_coords = np.zeros(num_points)
    return np.column_stack([x_coords, y_coords])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path, help="CSV produced by script 07.")
    parser.add_argument("--eps", type=float, default=0.09, help="DBSCAN eps parameter.")
    parser.add_argument("--min-samples", type=int, default=1, help="DBSCAN min_samples parameter.")
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=10,
        help="Minimum cluster size to display in the UMAP figure.",
    )
    parser.add_argument(
        "--cluster-output",
        type=Path,
        default=Path("results/clustering/dbscan_cluster_assignments.csv"),
        help="Output CSV for cluster assignments.",
    )
    parser.add_argument(
        "--plot-output",
        type=Path,
        default=Path("results/clustering/dbscan_umap.png"),
        help="Output PNG for the UMAP plot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.cluster_output.parent.mkdir(parents=True, exist_ok=True)
    args.plot_output.parent.mkdir(parents=True, exist_ok=True)

    average_dockq = pd.read_csv(args.input_csv)
    distance_matrix, unique_models = build_distance_matrix(average_dockq)
    num_models = len(unique_models)

    if num_models == 0:
        raise SystemExit("No model pairs were available for clustering.")

    dbscan = DBSCAN(eps=args.eps, min_samples=args.min_samples, metric="precomputed")
    cluster_labels = dbscan.fit_predict(distance_matrix)

    cluster_assignments = pd.DataFrame({"Model_PDB": unique_models, "Cluster": cluster_labels})
    cluster_assignments.to_csv(args.cluster_output, index=False)
    print(f"Wrote cluster assignments to {args.cluster_output}")

    if num_models < 3:
        embedding_scaled = fallback_embedding(num_models)
    else:
        n_neighbors = min(15, max(2, num_models - 1))
        try:
            reducer = umap.UMAP(
                n_neighbors=n_neighbors,
                min_dist=0.1,
                metric="precomputed",
                random_state=42,
            )
            embedding = reducer.fit_transform(distance_matrix)
            embedding_scaled = MinMaxScaler().fit_transform(embedding)
        except ValueError as exc:
            print(f"UMAP fallback triggered: {exc}")
            embedding_scaled = fallback_embedding(num_models)

    cluster_sizes = cluster_assignments["Cluster"].value_counts()
    visible_clusters = [
        cluster_id for cluster_id, size in cluster_sizes.items() if cluster_id != -1 and size >= args.min_cluster_size
    ]

    plt.figure(figsize=(12, 10))
    for cluster_id in visible_clusters:
        cluster_mask = cluster_assignments["Cluster"] == cluster_id
        points = embedding_scaled[cluster_mask.to_numpy()]
        plt.scatter(points[:, 0], points[:, 1], label=f"Cluster {cluster_id}")

    if not visible_clusters:
        plt.scatter(embedding_scaled[:, 0], embedding_scaled[:, 1], s=20, alpha=0.7)
        plt.title("UMAP visualization of DBSCAN clusters (no clusters met display threshold)")
    else:
        plt.title("UMAP visualization of DBSCAN clusters")
        plt.legend(loc="best")

    plt.xlabel("UMAP Dimension 1")
    plt.ylabel("UMAP Dimension 2")
    plt.tight_layout()
    plt.savefig(args.plot_output, dpi=300)
    print(f"Wrote UMAP plot to {args.plot_output}")


if __name__ == "__main__":
    main()
