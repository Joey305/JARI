"""Run pairwise DockQ comparisons across different model folders."""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from glob import glob
from multiprocessing import Pool, cpu_count
from pathlib import Path


FLOAT_PATTERN = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def count_clusters(directory_path: Path) -> int:
    return sum(1 for path in directory_path.iterdir() if path.is_dir() and path.name.startswith("cluster"))


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


def process_model_folder(args: tuple[Path, list[Path], Path, Path, Path, int]) -> None:
    model_folder, model_folders, models_dir, output_dir, dockq_executable, timeout = args
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{model_folder.name}_dockq_high_scores.txt"

    with output_file.open("w") as handle:
        handle.write("Model1\tCluster1\tPDB1\tModel2\tCluster2\tPDB2\tDockQ\tiRMS\tLRMS\n")

        for other_model_folder in model_folders:
            if model_folder == other_model_folder:
                continue

            model_cluster_count = count_clusters(models_dir / model_folder.name)
            other_cluster_count = count_clusters(models_dir / other_model_folder.name)

            for model_cluster_num in range(1, model_cluster_count + 1):
                for other_cluster_num in range(1, other_cluster_count + 1):
                    model_cluster_path = models_dir / model_folder.name / f"cluster{model_cluster_num}"
                    other_cluster_path = models_dir / other_model_folder.name / f"cluster{other_cluster_num}"

                    for model_pdb_file in get_pdb_files(model_cluster_path):
                        for other_model_pdb_file in get_pdb_files(other_cluster_path):
                            dockq, irms, lrms = execute_dockq_command(
                                dockq_executable,
                                model_pdb_file,
                                other_model_pdb_file,
                                timeout,
                            )
                            if dockq is None:
                                continue
                            line = (
                                f"{model_folder.name}\tcluster{model_cluster_num}\t{model_pdb_file.name}\t"
                                f"{other_model_folder.name}\tcluster{other_cluster_num}\t{other_model_pdb_file.name}\t"
                                f"{dockq}\t{irms}\t{lrms}\n"
                            )
                            handle.write(line)
                            print(line.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models_dir", type=Path, help="Directory containing model folders.")
    parser.add_argument(
        "--dockq-executable",
        type=Path,
        default=Path("./DockQ.py"),
        help="Path to the DockQ executable.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/cross_scores"),
        help="Directory where per-model cross-comparison text files are written.",
    )
    parser.add_argument("--processes", type=int, default=cpu_count(), help="Number of worker processes.")
    parser.add_argument("--timeout", type=int, default=120, help="Per-comparison timeout in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_folders = get_model_folders(args.models_dir)

    if not model_folders:
        raise SystemExit(f"No model folders found in {args.models_dir}")

    print(f"Total model folders to process: {len(model_folders)}")
    num_processes = max(1, min(len(model_folders), args.processes))

    with Pool(num_processes) as pool:
        pool.map(
            process_model_folder,
            [
                (folder, model_folders, args.models_dir, args.output_dir, args.dockq_executable, args.timeout)
                for folder in model_folders
            ],
        )

    print("All cross-model DockQ jobs completed.")


if __name__ == "__main__":
    start_time = time.time()
    main()
    duration = time.time() - start_time
    print(f"Script completed in {duration:.2f} seconds.")
