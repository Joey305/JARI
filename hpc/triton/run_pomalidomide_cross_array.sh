#!/usr/bin/env bash
# One LSF array task runs all cross-model comparisons for exactly one model.
set -euo pipefail

: "${POMA_MODELS_DIR:?Set POMA_MODELS_DIR to the prepared models directory}"
: "${POMA_RESULTS_DIR:?Set POMA_RESULTS_DIR to a writable results directory}"
: "${DOCKQ_EXECUTABLE:?Set DOCKQ_EXECUTABLE to DockQ.py or the DockQ executable}"
workers=${DOCKQ_WORKERS:-$(getconf _NPROCESSORS_ONLN)}

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
python_executable=${PYTHON_EXECUTABLE:-"$repo_root/.venv/bin/python"}
[[ -x "$python_executable" ]] || { echo "Python executable not found: $python_executable" >&2; exit 2; }
manifest="$POMA_MODELS_DIR/model_manifest.txt"
model_name=${POMA_MODEL_NAME:-}
if [[ -z "$model_name" ]]; then
  : "${LSB_JOBINDEX:?Set POMA_MODEL_NAME or launch this script from an LSF job array}"
  model_name=$(sed -n "${LSB_JOBINDEX}p" "$manifest")
fi
[[ -n "$model_name" ]] || { echo "No model selected" >&2; exit 2; }

"$python_executable" "$repo_root/scripts/02_run_cross_dockq.py" "$POMA_MODELS_DIR" \
  --model-name "$model_name" \
  --dockq-executable "$DOCKQ_EXECUTABLE" \
  --output-dir "$POMA_RESULTS_DIR/cross_scores" \
  --processes 1 \
  --comparison-workers "$workers" \
  --mapping AB:AB
