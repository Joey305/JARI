#!/usr/bin/env bash
# Submit 46 independent Pegasus jobs: one cross and one self task per PROTAC.
# Each task receives the full models directory and exactly one selected folder.
set -euo pipefail

: "${POMA_MODELS_DIR:?Set POMA_MODELS_DIR to the directory containing all PROTAC folders}"
: "${POMA_RESULTS_DIR:?Set POMA_RESULTS_DIR to a writable results directory}"
: "${DOCKQ_EXECUTABLE:?Set DOCKQ_EXECUTABLE to the DockQ executable}"

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
python_executable=${PYTHON_EXECUTABLE:-"$repo_root/.venv/bin/python"}
[[ -x "$python_executable" ]] || { echo "Python executable not found: $python_executable" >&2; exit 2; }
manifest="$POMA_MODELS_DIR/model_manifest.txt"
[[ -s "$manifest" ]] || { echo "Missing $manifest" >&2; exit 1; }
queue=${LSF_QUEUE:-normal}
mkdir -p "$POMA_RESULTS_DIR/logs"

while IFS= read -r model_name; do
  bsub -q "$queue" -n 1 -R 'span[hosts=1]' -J "poma_cross_${model_name}" \
    -oo "$POMA_RESULTS_DIR/logs/cross.${model_name}.%J.out" \
    -eo "$POMA_RESULTS_DIR/logs/cross.${model_name}.%J.err" \
    "$python_executable" "$repo_root/scripts/02_run_cross_dockq.py" "$POMA_MODELS_DIR" \
      --model-name "$model_name" --dockq-executable "$DOCKQ_EXECUTABLE" \
      --output-dir "$POMA_RESULTS_DIR/cross_scores" --processes 1 --comparison-workers 1 --mapping AB:AB
  bsub -q "$queue" -n 1 -R 'span[hosts=1]' -J "poma_self_${model_name}" \
    -oo "$POMA_RESULTS_DIR/logs/self.${model_name}.%J.out" \
    -eo "$POMA_RESULTS_DIR/logs/self.${model_name}.%J.err" \
    "$python_executable" "$repo_root/scripts/03_run_self_dockq.py" "$POMA_MODELS_DIR" \
      --model-name "$model_name" --dockq-executable "$DOCKQ_EXECUTABLE" \
      --output-dir "$POMA_RESULTS_DIR/self_scores" --processes 1 --comparison-workers 1 --mapping AB:AB
done < "$manifest"
