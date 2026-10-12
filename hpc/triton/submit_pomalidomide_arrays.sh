#!/usr/bin/env bash
# Submit the two 23-task (or manifest-sized) Pomalidomide DockQ LSF arrays.
set -euo pipefail

: "${POMA_MODELS_DIR:?Set POMA_MODELS_DIR to the prepared models directory}"
: "${POMA_RESULTS_DIR:?Set POMA_RESULTS_DIR to a writable results directory}"
: "${DOCKQ_EXECUTABLE:?Set DOCKQ_EXECUTABLE to DockQ.py or the DockQ executable}"

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
manifest="$POMA_MODELS_DIR/model_manifest.txt"
[[ -s "$manifest" ]] || { echo "Missing or empty $manifest; run prepare_pomalidomide_models.sh first." >&2; exit 1; }
task_count=$(wc -l < "$manifest")
# Triton's currently open general-purpose CPU queue is "normal". Override
# LSF_QUEUE only if your allocation has been instructed to use another queue.
queue=${LSF_QUEUE:-normal}
workers=${DOCKQ_WORKERS:-1}
[[ "$workers" =~ ^[1-9][0-9]*$ ]] || { echo "DOCKQ_WORKERS must be a positive integer." >&2; exit 2; }
mkdir -p "$POMA_RESULTS_DIR/logs"

# -env all passes the required path variables into the compute environment.
bsub -q "$queue" -J "poma_cross[1-${task_count}]" -n "$workers" -R 'span[hosts=1]' \
  -oo "$POMA_RESULTS_DIR/logs/cross.%J.%I.out" -eo "$POMA_RESULTS_DIR/logs/cross.%J.%I.err" \
  -env all bash "$repo_root/hpc/triton/run_pomalidomide_cross_array.sh"
bsub -q "$queue" -J "poma_self[1-${task_count}]" -n "$workers" -R 'span[hosts=1]' \
  -oo "$POMA_RESULTS_DIR/logs/self.%J.%I.out" -eo "$POMA_RESULTS_DIR/logs/self.%J.%I.err" \
  -env all bash "$repo_root/hpc/triton/run_pomalidomide_self_array.sh"
