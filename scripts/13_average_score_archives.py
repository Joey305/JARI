"""Average DockQ scores directly from score text archives or folders.

This is useful for large historical runs where the raw DockQ text reports are
available, but converting multi-gigabyte intermediates through Excel is slow.
The output schema matches ``07_average_pairwise_dockq.py``.
"""

from __future__ import annotations

import argparse
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path

import pandas as pd

from _cli_helpers import prompt_path


PDB1_ALIASES = ("PDB File 1", "PDB1")
PDB2_ALIASES = ("PDB File 2", "PDB2")


def iter_score_files(path: Path) -> Iterator[tuple[str, object]]:
    if path.is_dir():
        for txt_file in sorted(path.glob("*.txt")):
            with txt_file.open("rb") as handle:
                yield txt_file.name, handle
    elif path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = sorted(name for name in archive.namelist() if name.endswith(".txt"))
            for name in names:
                with archive.open(name) as handle:
                    yield Path(name).name, handle
    else:
        raise SystemExit(f"Expected a directory or .zip archive, got: {path}")


def first_existing(columns: Iterable[str], aliases: tuple[str, ...]) -> str | None:
    column_set = set(columns)
    return next((alias for alias in aliases if alias in column_set), None)


def model_name_from_self_filename(filename: str) -> str:
    return Path(filename).stem.replace("_self_scores", "")


def add_chunk_to_totals(
    chunk: pd.DataFrame,
    filename: str,
    totals: dict[str, list[float]],
    *,
    is_self_scores: bool,
) -> tuple[int, int]:
    if is_self_scores:
        model_name = model_name_from_self_filename(filename)
        chunk["Model1"] = model_name
        chunk["Model2"] = model_name

    pdb1_col = first_existing(chunk.columns, PDB1_ALIASES)
    pdb2_col = first_existing(chunk.columns, PDB2_ALIASES)
    required = ["Model1", "Model2", "DockQ"]
    missing = [column for column in required if column not in chunk.columns]
    if pdb1_col is None:
        missing.append("PDB File 1/PDB1")
    if pdb2_col is None:
        missing.append("PDB File 2/PDB2")
    if missing:
        raise SystemExit(f"{filename} is missing required columns: {', '.join(missing)}")

    valid_mask = chunk[["Model1", pdb1_col, "Model2", pdb2_col, "DockQ"]].notna().all(axis=1)
    valid = chunk.loc[valid_mask, ["Model1", pdb1_col, "Model2", pdb2_col, "DockQ"]].copy()
    if valid.empty:
        return 0, int((~valid_mask).sum())

    valid["DockQ"] = pd.to_numeric(valid["DockQ"], errors="coerce")
    valid = valid.dropna(subset=["DockQ"])
    valid[["Model1", pdb1_col, "Model2", pdb2_col]] = valid[
        ["Model1", pdb1_col, "Model2", pdb2_col]
    ].astype(str)

    pair_a = valid["Model1"] + "_" + valid[pdb1_col]
    pair_b = valid["Model2"] + "_" + valid[pdb2_col]
    valid["key"] = pd.Series(
        (("-".join(sorted((a, b))) for a, b in zip(pair_a, pair_b))),
        index=valid.index,
    )

    grouped = valid.groupby("key", sort=False)["DockQ"].agg(["sum", "count"])
    for key, row in grouped.iterrows():
        total = totals[key]
        total[0] += float(row["sum"])
        total[1] += int(row["count"])

    return len(valid), int((~valid_mask).sum())


def process_source(
    source: Path,
    totals: dict[str, list[float]],
    *,
    is_self_scores: bool,
    chunksize: int,
) -> tuple[int, int, int]:
    processed_files = 0
    processed_rows = 0
    skipped_rows = 0

    for filename, handle in iter_score_files(source):
        processed_files += 1
        file_rows = 0
        for chunk in pd.read_csv(handle, sep="\t", chunksize=chunksize):
            valid_count, skipped_count = add_chunk_to_totals(
                chunk,
                filename,
                totals,
                is_self_scores=is_self_scores,
            )
            processed_rows += valid_count
            skipped_rows += skipped_count
            file_rows += valid_count
        print(f"Processed {filename}: {file_rows:,} usable rows", flush=True)

    return processed_files, processed_rows, skipped_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("self_scores", type=Path, nargs="?", help="Self-score .zip archive or text directory.")
    parser.add_argument("cross_scores", type=Path, nargs="?", help="Cross-score .zip archive or text directory.")
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
        help="Output CSV summarizing rows skipped because required fields were absent.",
    )
    parser.add_argument("--chunksize", type=int, default=500_000, help="Rows to process per pandas chunk.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.self_scores = prompt_path(
        "Enter the self-score ZIP archive or directory",
        args.self_scores,
        must_exist=True,
        expect_dir=None,
    )
    args.cross_scores = prompt_path(
        "Enter the cross-score ZIP archive or directory",
        args.cross_scores,
        must_exist=True,
        expect_dir=None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.unpaired_output.parent.mkdir(parents=True, exist_ok=True)

    totals: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    self_file_count, self_rows, self_skipped = process_source(
        args.self_scores,
        totals,
        is_self_scores=True,
        chunksize=args.chunksize,
    )
    cross_file_count, cross_rows, cross_skipped = process_source(
        args.cross_scores,
        totals,
        is_self_scores=False,
        chunksize=args.chunksize,
    )

    averaged = pd.DataFrame(
        ((key, total / count) for key, (total, count) in totals.items()),
        columns=["key", "Average_DockQ"],
    )
    averaged.to_csv(args.output, index=False)

    skipped_summary = pd.DataFrame(
        [
            {"Source": "self_scores", "Files": self_file_count, "Usable Rows": self_rows, "Skipped Rows": self_skipped},
            {"Source": "cross_scores", "Files": cross_file_count, "Usable Rows": cross_rows, "Skipped Rows": cross_skipped},
        ]
    )
    skipped_summary.to_csv(args.unpaired_output, index=False)

    print(f"Wrote averaged scores to {args.output}", flush=True)
    print(f"Wrote skipped-row summary to {args.unpaired_output}", flush=True)
    print(
        f"Averaged {len(averaged):,} unique unordered pairs from {self_rows + cross_rows:,} usable rows",
        flush=True,
    )


if __name__ == "__main__":
    main()
