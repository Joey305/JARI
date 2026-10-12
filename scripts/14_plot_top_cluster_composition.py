"""Plot the model-family composition of a selected JARI cluster.

The default behavior selects the highest-population non-noise DBSCAN cluster,
groups its structures by model family, highlights the top model families, and
draws family-family edges supported by high-similarity averaged DockQ pairs.
"""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from _cli_helpers import prompt_path


COMBINED_PDB_PATTERN = re.compile(r"(.+?)_combined_.*\.pdb$")


def model_family(model_pdb: str) -> str:
    match = COMBINED_PDB_PATTERN.match(model_pdb)
    if match:
        return match.group(1)
    return model_pdb.removesuffix(".pdb")


def excel_style_code(index: int) -> str:
    letters = []
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def choose_cluster(cluster_assignments: pd.DataFrame, cluster_id: int | None) -> int:
    if cluster_id is not None:
        if cluster_id not in set(cluster_assignments["Cluster"]):
            raise SystemExit(f"Cluster {cluster_id} is not present in the cluster assignment table.")
        return cluster_id

    non_noise = cluster_assignments.loc[cluster_assignments["Cluster"] != -1, "Cluster"]
    cluster_counts = non_noise.value_counts() if not non_noise.empty else cluster_assignments["Cluster"].value_counts()
    if cluster_counts.empty:
        raise SystemExit("No cluster assignments were found.")
    return int(cluster_counts.idxmax())


def load_cluster_composition(cluster_path: Path, cluster_id: int | None, top_n: int) -> tuple[int, pd.DataFrame, set[str], dict[str, str]]:
    cluster_assignments = pd.read_csv(cluster_path)
    required = {"Model_PDB", "Cluster"}
    missing = required.difference(cluster_assignments.columns)
    if missing:
        raise SystemExit(f"{cluster_path} is missing required columns: {', '.join(sorted(missing))}")

    selected_cluster = choose_cluster(cluster_assignments, cluster_id)
    cluster_members = cluster_assignments[cluster_assignments["Cluster"] == selected_cluster].copy()
    if cluster_members.empty:
        raise SystemExit(f"Cluster {selected_cluster} has no members.")

    cluster_members["Family"] = cluster_members["Model_PDB"].map(model_family)
    composition = (
        cluster_members["Family"]
        .value_counts()
        .rename_axis("Family")
        .reset_index(name="Count")
        .sort_values(["Count", "Family"], ascending=[False, True], ignore_index=True)
    )
    composition["Code"] = [excel_style_code(index) for index in range(len(composition))]
    composition["Highlighted"] = composition.index < top_n

    family_by_model_pdb = dict(zip(cluster_members["Model_PDB"], cluster_members["Family"]))
    return selected_cluster, composition, set(cluster_members["Model_PDB"]), family_by_model_pdb


def collect_family_edges(
    averaged_scores_path: Path,
    cluster_members: set[str],
    family_by_model_pdb: dict[str, str],
    *,
    edge_threshold: float,
    min_edge_pairs: int,
    chunksize: int,
) -> pd.DataFrame:
    edge_stats: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0, 0.0, 0.0])

    for chunk in pd.read_csv(averaged_scores_path, chunksize=chunksize):
        if "key" not in chunk.columns or "Average_DockQ" not in chunk.columns:
            raise SystemExit(f"{averaged_scores_path} must contain key and Average_DockQ columns.")

        split_pairs = chunk["key"].str.split("-", n=1, expand=True)
        mask = (
            split_pairs[0].isin(cluster_members)
            & split_pairs[1].isin(cluster_members)
            & split_pairs[0].ne(split_pairs[1])
            & (chunk["Average_DockQ"] >= edge_threshold)
        )
        if not mask.any():
            continue

        selected_scores = chunk.loc[mask, "Average_DockQ"].to_numpy()
        left_items = split_pairs.loc[mask, 0].to_numpy()
        right_items = split_pairs.loc[mask, 1].to_numpy()

        for left_item, right_item, score in zip(left_items, right_items, selected_scores):
            left_family = family_by_model_pdb[left_item]
            right_family = family_by_model_pdb[right_item]
            if left_family == right_family:
                continue
            edge_key = tuple(sorted((left_family, right_family)))
            stats = edge_stats[edge_key]
            stats[0] += 1
            stats[1] += float(score)
            stats[2] = max(stats[2], float(score))

    rows = []
    for (left_family, right_family), (count, score_sum, max_score) in edge_stats.items():
        if count < min_edge_pairs:
            continue
        rows.append(
            {
                "Family 1": left_family,
                "Family 2": right_family,
                "Pair Count": int(count),
                "Mean Average_DockQ": score_sum / count,
                "Max Average_DockQ": max_score,
            }
        )

    return pd.DataFrame(rows).sort_values(["Pair Count", "Family 1", "Family 2"], ascending=[False, True, True])


def spring_layout(
    families: list[str],
    edges: pd.DataFrame,
    counts: dict[str, int],
    *,
    seed: int,
    iterations: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    node_count = len(families)
    if node_count == 1:
        return {families[0]: np.array([0.5, 0.5])}

    angles = np.linspace(0, 2 * np.pi, node_count, endpoint=False)
    positions = np.column_stack((np.cos(angles), np.sin(angles))) * 0.35 + 0.5
    positions += rng.normal(0, 0.02, positions.shape)

    index_by_family = {family: index for index, family in enumerate(families)}
    edge_records = []
    if not edges.empty:
        max_pair_count = edges["Pair Count"].max()
        for _, row in edges.iterrows():
            edge_records.append(
                (
                    index_by_family[row["Family 1"]],
                    index_by_family[row["Family 2"]],
                    0.2 + 0.8 * (row["Pair Count"] / max_pair_count),
                )
            )

    preferred_radius = 0.28 + 0.18 * (1 - np.array([counts[family] for family in families]) / max(counts.values()))
    temperature = 0.08
    for _ in range(iterations):
        displacement = np.zeros_like(positions)
        for i in range(node_count):
            delta = positions[i] - positions
            distance = np.linalg.norm(delta, axis=1) + 1e-6
            repulsion = (0.0011 / distance**2)[:, None] * delta / distance[:, None]
            displacement[i] += repulsion.sum(axis=0)

        for left_index, right_index, weight in edge_records:
            delta = positions[right_index] - positions[left_index]
            distance = np.linalg.norm(delta) + 1e-6
            attraction = weight * 0.035 * math.log1p(distance / 0.2) * delta / distance
            displacement[left_index] += attraction
            displacement[right_index] -= attraction

        center_delta = np.array([0.5, 0.5]) - positions
        displacement += 0.08 * center_delta
        radial = positions - np.array([0.5, 0.5])
        radial_distance = np.linalg.norm(radial, axis=1) + 1e-6
        displacement += ((preferred_radius - radial_distance) * 0.08)[:, None] * radial / radial_distance[:, None]

        step = np.clip(displacement, -temperature, temperature)
        positions = np.clip(positions + step, 0.12, 0.88)
        temperature *= 0.985

    return {family: positions[index] for family, index in index_by_family.items()}


def add_panel_box(ax: plt.Axes) -> None:
    panel = FancyBboxPatch(
        (-0.04, -0.08),
        1.08,
        1.17,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        transform=ax.transAxes,
        fc="white",
        ec="#cfd6de",
        lw=1.2,
        zorder=-10,
        clip_on=False,
    )
    ax.add_patch(panel)


def add_panel_letter(ax: plt.Axes, letter: str) -> None:
    ax.text(
        0.0,
        1.03,
        letter,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="circle,pad=0.45", fc="#df1022", ec="#df1022"),
    )


def draw_network_panel(
    ax: plt.Axes,
    composition: pd.DataFrame,
    edges: pd.DataFrame,
    *,
    seed: int,
    layout_iterations: int,
) -> None:
    add_panel_box(ax)
    add_panel_letter(ax, "A")
    ax.set_title("Structural-similarity network of the top JARI cluster", fontsize=13, fontweight="bold", pad=24)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    families = composition["Family"].tolist()
    counts = dict(zip(composition["Family"], composition["Count"]))
    codes = dict(zip(composition["Family"], composition["Code"]))
    highlighted = set(composition.loc[composition["Highlighted"], "Family"])
    positions = spring_layout(families, edges, counts, seed=seed, iterations=layout_iterations)

    max_edge_count = edges["Pair Count"].max() if not edges.empty else 1
    for _, edge in edges.iterrows():
        start = positions[edge["Family 1"]]
        end = positions[edge["Family 2"]]
        width = 0.35 + 2.4 * math.sqrt(edge["Pair Count"] / max_edge_count)
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color="#111820",
            lw=width,
            alpha=0.22,
            solid_capstyle="round",
            zorder=1,
        )

    max_count = max(counts.values())
    min_count = min(counts.values())
    count_span = max(1, max_count - min_count)
    for family in families:
        x, y = positions[family]
        count = counts[family]
        size = 650 + 2800 * ((count - min_count) / count_span) ** 0.75
        color = "#ffd200" if family in highlighted else "#9ddae8"
        ax.scatter([x], [y], s=size, c=color, edgecolors="#5d6670", linewidths=0.8, zorder=3)
        ax.text(
            x,
            y,
            f"{codes[family]}\n({count})",
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color="#111820",
            zorder=4,
        )


def draw_bar_panel(ax: plt.Axes, composition: pd.DataFrame) -> None:
    add_panel_box(ax)
    add_panel_letter(ax, "B")
    ax.set_title("Model composition of the top JARI cluster", fontsize=13, fontweight="bold", pad=24)

    colors = ["#ffd200" if value else "#117db5" for value in composition["Highlighted"]]
    ax.bar(composition["Code"], composition["Count"], color=colors, edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Model")
    ax.set_ylabel("Count")
    ax.grid(axis="y", color="#d9dee5", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelrotation=90, labelsize=7)
    ax.tick_params(axis="y", labelsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def write_summary_tables(composition: pd.DataFrame, edges: pd.DataFrame, output_path: Path) -> None:
    stem = output_path.with_suffix("")
    composition.to_csv(stem.with_name(stem.name + "_composition.csv"), index=False)
    edges.to_csv(stem.with_name(stem.name + "_edges.csv"), index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cluster-assignments",
        type=Path,
        default=Path("results/clustering/dbscan_cluster_assignments.csv"),
        help="CSV produced by 11_cluster_dbscan_umap.py.",
    )
    parser.add_argument(
        "--averaged-scores",
        type=Path,
        default=Path("results/tables/averaged_dockq_scores.csv"),
        help="CSV produced by 07_average_pairwise_dockq.py or 13_average_score_archives.py.",
    )
    parser.add_argument("--cluster-id", type=int, default=None, help="Cluster ID to plot. Defaults to the largest non-noise cluster.")
    parser.add_argument("--top-n", type=int, default=5, help="Number of model families to highlight in yellow.")
    parser.add_argument("--edge-threshold", type=float, default=0.91, help="Minimum Average_DockQ required to draw an edge.")
    parser.add_argument("--min-edge-pairs", type=int, default=1, help="Minimum supporting PDB pairs required for an edge.")
    parser.add_argument("--chunksize", type=int, default=500_000, help="Rows to read at a time from the averaged score CSV.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic network layout.")
    parser.add_argument("--layout-iterations", type=int, default=500, help="Iterations for the built-in force layout.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/clustering/top_cluster_composition_network.png"),
        help="Output PNG path for the combined figure.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.cluster_assignments = prompt_path(
        "Enter the DBSCAN cluster assignment CSV",
        args.cluster_assignments,
        must_exist=True,
        expect_dir=False,
    )
    args.averaged_scores = prompt_path(
        "Enter the averaged DockQ score CSV",
        args.averaged_scores,
        must_exist=True,
        expect_dir=False,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected_cluster, composition, cluster_members, family_by_model_pdb = load_cluster_composition(
        args.cluster_assignments,
        args.cluster_id,
        args.top_n,
    )
    edges = collect_family_edges(
        args.averaged_scores,
        cluster_members,
        family_by_model_pdb,
        edge_threshold=args.edge_threshold,
        min_edge_pairs=args.min_edge_pairs,
        chunksize=args.chunksize,
    )

    code_by_family = dict(zip(composition["Family"], composition["Code"]))
    if not edges.empty:
        edges = edges.assign(
            **{
                "Code 1": edges["Family 1"].map(code_by_family),
                "Code 2": edges["Family 2"].map(code_by_family),
            }
        )
        edges = edges[["Code 1", "Code 2", "Family 1", "Family 2", "Pair Count", "Mean Average_DockQ", "Max Average_DockQ"]]

    fig, (network_ax, bar_ax) = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={"width_ratios": [1, 1.08]})
    fig.patch.set_facecolor("white")
    draw_network_panel(network_ax, composition, edges, seed=args.seed, layout_iterations=args.layout_iterations)
    draw_bar_panel(bar_ax, composition)

    cluster_size = int(composition["Count"].sum())
    fig.text(
        0.035,
        0.96,
        "JARI clustering of PRosettaC-derived ternary-complex models",
        fontsize=24,
        fontweight="bold",
        color="#15202b",
    )
    fig.text(
        0.035,
        0.92,
        f"Cluster {selected_cluster}: highest-population structural cluster and its model composition",
        fontsize=12.5,
        color="#5b6673",
    )
    fig.lines.append(
        plt.Line2D([0.035, 0.965], [0.905, 0.905], transform=fig.transFigure, color="#cfd6de", lw=1)
    )
    fig.text(
        0.5,
        0.035,
        (
            f"Cluster size: {cluster_size} structures. Node size and bar height reflect model-family counts. "
            f"Yellow marks the top {args.top_n} families. Edges require Average_DockQ >= {args.edge_threshold:g}; "
            "line width scales with the number of supporting structure pairs."
        ),
        ha="center",
        va="center",
        fontsize=8,
        color="#4f5b66",
        bbox=dict(boxstyle="round,pad=0.35", fc="#f1f4f7", ec="none"),
    )

    plt.tight_layout(rect=[0.02, 0.07, 0.98, 0.885])
    fig.savefig(args.output, dpi=300, bbox_inches="tight")
    write_summary_tables(composition, edges, args.output)

    print(f"Selected cluster {selected_cluster} with {cluster_size} structures across {len(composition)} model families.")
    print(f"Highlighted top {args.top_n} model families.")
    print(f"Wrote figure to {args.output}")
    print(f"Wrote composition CSV to {args.output.with_suffix('').with_name(args.output.with_suffix('').name + '_composition.csv')}")
    print(f"Wrote edge CSV to {args.output.with_suffix('').with_name(args.output.with_suffix('').name + '_edges.csv')}")


if __name__ == "__main__":
    main()
