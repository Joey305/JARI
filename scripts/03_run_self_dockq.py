"""Run DockQ comparisons within each model folder."""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from glob import glob
from multiprocessing import Pool, cpu_count
from pathlib import Path

from _cli_helpers import prompt_path


FLOAT_PATTERN = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def resolve_model_results_dir(model_dir: Path) -> Path:
    results_dir = model_dir / "Results"
    return results_dir if results_dir.is_dir() else model_dir


def get_cluster_dirs(model_dir: Path) -> list[Path]:
    results_dir = resolve_model_results_dir(model_dir)
    return sorted(path for path in results_dir.iterdir() if path.is_dir() and path.name.startswith("cluster"))


def get_pdb_files(directory_path: Path) -> list[Path]:
    return [Path(path) for path in sorted(glob(str(directory_path / "*.pdb")))]


def parse_metric(output: str, name: str) -> str | None:
    match = re.search(rf"\b{name}\b.*?({FLOAT_PATTERN})", output)
    return match.group(1) if match else None


def execute_dockq_command(dockq_executable: Path, native_pdb: Path, model_pdb: Path, timeout: int) -> tuple[str | None, str | None, str | None]:
    cmd = [str(dockq_executable), str(native_pdb), str(model_pdb)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"DockQ failed for {native_pdb.name} vs {model_pdb.name}")
        print(exc.stdout)
        print(exc.stderr)
        return None, None, None
    except subprocess.TimeoutExpired:
        print(f"DockQ timed out for {native_pdb.name} vs {model_pdb.name}")
        return None, None, None

    output = result.stdout + "\n" + result.stderr
    return parse_metric(output, "DockQ"), parse_metric(output, "iRMS"), parse_metric(output, "LRMS")


def get_model_folders(directory: Path) -> list[Path]:
    return sorted(path for path in directory.iterdir() if path.is_dir())


def process_model_folder(args: tuple[Path, Path, Path, Path, int]) -> None:
    model_folder, models_dir, output_dir, dockq_executable, timeout = args
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{model_folder.name}_self_scores.txt"
    model_root = models_dir / model_folder.name
    cluster_dirs = get_cluster_dirs(model_root)

    with output_file.open("w") as handle:
        handle.write("Cluster1\tPDB File 1\tCluster2\tPDB File 2\tDockQ\tiRMS\tLRMS\n")

        for cluster_index1, cluster_path1 in enumerate(cluster_dirs):
            pdb_files1 = get_pdb_files(cluster_path1)

            for cluster_index2 in range(cluster_index1, len(cluster_dirs)):
                cluster_path2 = cluster_dirs[cluster_index2]
                pdb_files2 = get_pdb_files(cluster_path2) if cluster_index1 != cluster_index2 else pdb_files1

                for pdb_file1 in pdb_files1:
                    for pdb_file2 in pdb_files2:
                        if cluster_index1 == cluster_index2 and pdb_file1 == pdb_file2:
                            continue

                        dockq, irms, lrms = execute_dockq_command(dockq_executable, pdb_file1, pdb_file2, timeout)
                        if dockq is None:
                            continue

                        line = (
                            f"{cluster_path1.name}\t{pdb_file1.name}\t{cluster_path2.name}\t{pdb_file2.name}\t"
                            f"{dockq}\t{irms}\t{lrms}\n"
                        )
                        handle.write(line)
                        print(line.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models_dir", type=Path, nargs="?", help="Directory containing model folders.")
    parser.add_argument(
        "--dockq-executable",
        type=Path,
        default=Path("./DockQ.py"),
        help="Path to the DockQ executable.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/self_scores"),
        help="Directory where per-model self-comparison text files are written.",
    )
    parser.add_argument("--processes", type=int, default=cpu_count(), help="Number of worker processes.")
    parser.add_argument("--timeout", type=int, default=120, help="Per-comparison timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.models_dir = prompt_path(
        "Enter the PRosettaC models directory",
        args.models_dir,
        must_exist=True,
        expect_dir=True,
    )
    if not args.dockq_executable.exists():
        args.dockq_executable = prompt_path(
            "Enter the path to DockQ.py",
            None,
            must_exist=True,
            expect_dir=False,
            default=str(args.dockq_executable),
        )
    model_folders = get_model_folders(args.models_dir)

    if not model_folders:
        raise SystemExit(f"No model folders found in {args.models_dir}")

    print(f"Total model folders to process: {len(model_folders)}")
    num_processes = max(1, min(len(model_folders), args.processes))

    with Pool(num_processes) as pool:
        pool.map(
            process_model_folder,
            [
                (folder, args.models_dir, args.output_dir, args.dockq_executable, args.timeout)
                for folder in model_folders
            ],
        )

    print("All self-model DockQ jobs completed.")


if __name__ == "__main__":
    start_time = time.time()
    main()
    duration = time.time() - start_time
    print(f"Script completed in {duration:.2f} seconds.")
