#!/usr/bin/env bash
# Expand the supplied archives into one model directory per archive.  DockQ v2
# scores the PRosettaC PDBs directly; no PDB rewriting is performed.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 ARCHIVE_DIRECTORY MODELS_DIRECTORY" >&2
  exit 2
fi

archive_dir=$1
models_dir=$2
mkdir -p "$models_dir"
shopt -s nullglob
archives=("$archive_dir"/*_Results.zip)
if (( ${#archives[@]} == 0 )); then
  echo "No *_Results.zip files found in $archive_dir" >&2
  exit 1
fi

for archive in "${archives[@]}"; do
  model_name=$(basename "$archive" _Results.zip)
  model_dir="$models_dir/$model_name"
  if [[ -e "$model_dir" ]]; then
    echo "Refusing to overwrite existing $model_dir" >&2
    exit 1
  fi
  mkdir -p "$model_dir"
  unzip -q "$archive" -d "$model_dir"
done

find "$models_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | LC_ALL=C sort > "$models_dir/model_manifest.txt"
echo "Staged $(wc -l < "$models_dir/model_manifest.txt") raw models."
