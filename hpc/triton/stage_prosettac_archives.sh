#!/usr/bin/env bash
# Expand PRosettaC ZIPs into short, scheduler-safe model keys (M001, M002, ...).
# Original archive labels remain in archive_manifest.tsv for later annotation.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 ZIP_DIRECTORY MODELS_DIRECTORY" >&2
  exit 2
fi

zip_dir=$1
models_dir=$2
[[ -d "$zip_dir" ]] || { echo "ZIP directory not found: $zip_dir" >&2; exit 1; }
mkdir -p "$models_dir"

input_manifest=$(mktemp)
expected_manifest=$(mktemp)
trap 'rm -f "$input_manifest" "$expected_manifest"' EXIT

# Archive names may be long; only reject tabs/newlines, which cannot be safely
# represented in the tab-separated provenance manifest.
while IFS= read -r -d '' archive; do
  archive_name=$(basename "$archive")
  [[ "$archive_name" != *$'\t'* && "$archive_name" != *$'\n'* ]] || {
    echo "Archive names cannot contain tabs or newlines: $archive_name" >&2
    exit 1
  }
  label=${archive_name%.zip}
  label=${label%_Results}
  printf '%s\t%s\t%s\n' "$archive_name" "$label" "$(sha256sum "$archive" | awk '{print $1}')" >> "$input_manifest"
done < <(find "$zip_dir" -maxdepth 1 -type f -name '*.zip' -print0 | sort -z)

[[ -s "$input_manifest" ]] || { echo "No .zip files found directly in $zip_dir" >&2; exit 1; }

counter=0
while IFS=$'\t' read -r archive_name label sha256; do
  counter=$((counter + 1))
  printf 'M%03d\t%s\t%s\t%s\n' "$counter" "$label" "$archive_name" "$sha256" >> "$expected_manifest"
done < "$input_manifest"

archive_manifest="$models_dir/archive_manifest.tsv"
if [[ -f "$archive_manifest" ]]; then
  # A run is immutable: silently changing its inputs could pair old scores with
  # different structures. Use a new jari-run --name for a changed ZIP set.
  tail -n +2 "$archive_manifest" > "$input_manifest.existing"
  if ! cmp -s "$expected_manifest" "$input_manifest.existing"; then
    echo "The ZIP set differs from the existing run. Use a new --name instead of changing this run." >&2
    rm -f "$input_manifest.existing"
    exit 1
  fi
  rm -f "$input_manifest.existing"
fi

printf 'model_key\toriginal_label\tarchive_name\tsha256\n' > "$archive_manifest"
while IFS=$'\t' read -r model_key label archive_name sha256; do
  archive="$zip_dir/$archive_name"
  model_dir="$models_dir/$model_key"
  if [[ -e "$model_dir" ]]; then
    find "$model_dir" -type f -name '*.pdb' -print -quit | grep -q . || {
      echo "Existing model directory has no PDBs: $model_dir" >&2
      exit 1
    }
    echo "Keeping $model_key ($label)"
  else
    mkdir -p "$model_dir"
    unzip -q "$archive" -d "$model_dir"
    find "$model_dir" -type f -name '*.pdb' -print -quit | grep -q . || {
      echo "No PDB files found after extracting $archive_name" >&2
      exit 1
    }
    echo "Staged $model_key ($label)"
  fi
  printf '%s\t%s\t%s\t%s\n' "$model_key" "$label" "$archive_name" "$sha256" >> "$archive_manifest"
done < "$expected_manifest"

cut -f1 "$expected_manifest" > "$models_dir/model_manifest.txt"
echo "Ready: $counter PRosettaC models in $models_dir"
