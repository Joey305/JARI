"""Run DockQ comparisons within each model folder."""

from __future__ import annotations

import argparse
from itertools import islice
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
    # DockQ v2 prints a score-quality legend before the actual metric lines.
    # Require a metric line that starts with the requested name; otherwise the
    # legend's "0.23 <= DockQ" threshold is mistakenly parsed as every score.
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*(?::|=|\s)\s*({FLOAT_PATTERN})\b", output)
    return match.group(1) if match else None


def execute_dockq_command(
    dockq_executable: Path,
    native_pdb: Path,
    model_pdb: Path,
    timeout: int,
    mapping: str | None,
) -> tuple[str | None, str | None, str | None]:
    cmd = [str(dockq_executable), str(native_pdb), str(model_pdb)]
    if mapping:
        cmd.extend(["--mapping", mapping])
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
    # DockQ v2 labels these metrics iRMSD and LRMSD; retain the v1 fallbacks
    # so older installations remain usable.
    return (
        parse_metric(output, "DockQ"),
        parse_metric(output, "iRMSD") or parse_metric(output, "iRMS"),
        parse_metric(output, "LRMSD") or parse_metric(output, "LRMS"),
    )


def get_model_folders(directory: Path) -> list[Path]:
    return sorted(path for path in directory.iterdir() if path.is_dir())


def score_self_task(task: tuple[str, str, Path, Path, int, str | None]) -> str | None:
    cluster_name1, pdb_name1, cluster_name2, pdb_name2, dockq_executable, timeout, mapping = task
    dockq, irms, lrms = execute_dockq_command(
        dockq_executable, Path(pdb_name1), Path(pdb_name2), timeout, mapping
    )
    return (
        f"{cluster_name1}\t{Path(pdb_name1).name}\t{cluster_name2}\t{Path(pdb_name2).name}\t"
        f"{dockq or 'NA'}\t{irms or 'NA'}\t{lrms or 'NA'}\n"
    )


def iter_self_tasks(model_root: Path, dockq_executable: Path, timeout: int, mapping: str | None):
    cluster_dirs = get_cluster_dirs(model_root)
    for cluster_index1, cluster_path1 in enumerate(cluster_dirs):
        pdb_files1 = get_pdb_files(cluster_path1)
        for cluster_index2 in range(cluster_index1, len(cluster_dirs)):
            cluster_path2 = cluster_dirs[cluster_index2]
            pdb_files2 = get_pdb_files(cluster_path2) if cluster_index1 != cluster_index2 else pdb_files1
            for pdb_file1 in pdb_files1:
                for pdb_file2 in pdb_files2:
                    if cluster_index1 == cluster_index2 and pdb_file1 == pdb_file2:
                        continue
                    yield (
                        cluster_path1.name, str(pdb_file1), cluster_path2.name, str(pdb_file2),
                        dockq_executable, timeout, mapping,
                    )


def existing_score_count(output_file: Path) -> int:
    """Count completed data rows without loading a large score file into memory."""
    with output_file.open() as handle:
        return max(0, sum(1 for _ in handle) - 1)


def process_model_folder(args: tuple[Path, Path, Path, Path, int, int, str | None, bool, bool]) -> None:
    model_folder, models_dir, output_dir, dockq_executable, timeout, comparison_workers, mapping, verbose, resume = args
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{model_folder.name}_self_scores.txt"
    model_root = models_dir / model_folder.name

    completed_count = existing_score_count(output_file) if resume and output_file.exists() else 0
    with output_file.open("a" if completed_count else "w", buffering=1) as handle:
        if not completed_count:
            handle.write("Cluster1\tPDB File 1\tCluster2\tPDB File 2\tDockQ\tiRMS\tLRMS\n")
        elif verbose:
            print(f"Resuming after {completed_count:,} completed comparisons.")
        tasks = islice(iter_self_tasks(model_root, dockq_executable, timeout, mapping), completed_count, None)
        if comparison_workers == 1:
            scored_lines = map(score_self_task, tasks)
            for line in scored_lines:
                handle.write(line)
                if verbose:
                    print(line.strip())
        else:
            with Pool(comparison_workers) as pool:
                for line in pool.imap_unordered(score_self_task, tasks, chunksize=16):
                    handle.write(line)
                    if verbose:
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
    parser.add_argument(
        "--comparison-workers",
        type=int,
        default=1,
        help="Concurrent DockQ comparisons within each selected model folder.",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Per-comparison timeout in seconds.")
    parser.add_argument("--mapping", help="Optional DockQ model:native chain mapping, e.g. AB:AB.")
    parser.add_argument("--verbose", action="store_true", help="Print every completed comparison.")
    parser.add_argument("--resume", action="store_true", help="Append to existing output and skip its completed rows.")
    parser.add_argument(
        "--model-name",
        help="Run only this top-level model folder. Intended for one-task-per-model scheduler jobs.",
    )
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

    selected_folders = model_folders
    if args.model_name:
        selected_folders = [folder for folder in model_folders if folder.name == args.model_name]
        if not selected_folders:
            raise SystemExit(
                f"No model folder named {args.model_name!r} found in {args.models_dir}"
            )

    print(f"Total model folders to process: {len(selected_folders)} of {len(model_folders)}")
    num_processes = max(1, min(len(selected_folders), args.processes))
    if args.comparison_workers < 1:
        raise SystemExit("--comparison-workers must be at least 1")
    if args.comparison_workers > 1 and num_processes > 1:
        raise SystemExit("Use --processes 1 when --comparison-workers is greater than 1.")
    if args.resume and args.comparison_workers > 1:
        raise SystemExit("--resume requires --comparison-workers 1 for deterministic ordering.")

    job_args = [
        (
            folder, args.models_dir, args.output_dir, args.dockq_executable,
            args.timeout, args.comparison_workers, args.mapping, args.verbose, args.resume,
        )
        for folder in selected_folders
    ]
    if num_processes == 1:
        process_model_folder(job_args[0])
    else:
        with Pool(num_processes) as pool:
            pool.map(process_model_folder, job_args)

    print("All self-model DockQ jobs completed.")


if __name__ == "__main__":
    start_time = time.time()
    main()
    duration = time.time() - start_time
    print(f"Script completed in {duration:.2f} seconds.")
