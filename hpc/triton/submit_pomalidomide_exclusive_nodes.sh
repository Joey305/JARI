#!/usr/bin/env bash
# Submit 46 independent exclusive-node jobs: one cross and one self job per model.
set -euo pipefail

: "${POMA_MODELS_DIR:?Set POMA_MODELS_DIR to the prepared models directory}"
: "${POMA_RESULTS_DIR:?Set POMA_RESULTS_DIR to a writable results directory}"
: "${DOCKQ_EXECUTABLE:?Set DOCKQ_EXECUTABLE to the DockQ executable}"

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
manifest="$POMA_MODELS_DIR/model_manifest.txt"
[[ -s "$manifest" ]] || { echo "Missing $manifest" >&2; exit 1; }
queue=${LSF_QUEUE:-normal}
export DOCKQ_WORKERS=${DOCKQ_WORKERS:-$(getconf _NPROCESSORS_ONLN)}
mkdir -p "$POMA_RESULTS_DIR/logs"

while IFS= read -r model_name; do
  export POMA_MODEL_NAME="$model_name"
  bsub -q "$queue" -x -n 1 -R 'span[hosts=1]' -J "poma_cross_${model_name}" \
    -oo "$POMA_RESULTS_DIR/logs/cross.${model_name}.%J.out" \
    -eo "$POMA_RESULTS_DIR/logs/cross.${model_name}.%J.err" \
    -env all bash "$repo_root/hpc/triton/run_pomalidomide_cross_array.sh"
  bsub -q "$queue" -x -n 1 -R 'span[hosts=1]' -J "poma_self_${model_name}" \
    -oo "$POMA_RESULTS_DIR/logs/self.${model_name}.%J.out" \
    -eo "$POMA_RESULTS_DIR/logs/self.${model_name}.%J.err" \
    -env all bash "$repo_root/hpc/triton/run_pomalidomide_self_array.sh"
done < "$manifest"
