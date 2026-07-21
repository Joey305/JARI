"""Prepare PyRosettaC PDB outputs for downstream DockQ scoring.

This script updates each matching PDB file by:
1. incrementing residue numbers for atoms in chain B, and
2. converting HETATM records in chain X into chain B.

The expected input layout is:

    models_dir/
      model_a/
        cluster1/
          combined_*.pdb
        cluster2/
          combined_*.pdb
      model_b/
        ...
"""

from __future__ import annotations

import argparse
from pathlib import Path


def modify_pdb_file(file_path: Path) -> None:
    lines = file_path.read_text().splitlines(keepends=True)

    with file_path.open("w") as handle:
        for line in lines:
            if line.startswith("ATOM") and line[21] == "B":
                residue_number = int(line[22:26]) + 1
                line = line[:22] + f"{residue_number:4d}" + line[26:]
            elif line.startswith("HETATM") and line[21] == "X":
                line = line[:21] + "B" + line[22:]
            handle.write(line)


def iter_cluster_pdbs(models_dir: Path, pdb_pattern: str) -> list[Path]:
    pdb_files: list[Path] = []
    for cluster_dir in sorted(models_dir.glob("*/cluster*")):
        if cluster_dir.is_dir():
            pdb_files.extend(sorted(cluster_dir.glob(pdb_pattern)))
    return pdb_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "models_dir",
        type=Path,
        help="Directory containing model folders with cluster subdirectories.",
    )
    parser.add_argument(
        "--pdb-pattern",
        default="combined*.pdb",
        help="Glob pattern used to find PDB files inside cluster folders.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdb_files = iter_cluster_pdbs(args.models_dir, args.pdb_pattern)

    if not pdb_files:
        raise SystemExit(f"No PDB files matching {args.pdb_pattern!r} found in {args.models_dir}")

    for pdb_file in pdb_files:
        print(f"Preparing {pdb_file}")
        modify_pdb_file(pdb_file)

    print(f"Updated {len(pdb_files)} PDB files.")


if __name__ == "__main__":
    main()
