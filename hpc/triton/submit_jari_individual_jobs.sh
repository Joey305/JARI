#!/usr/bin/env bash
# Submit one resumable cross and one resumable self DockQ job per PRosettaC model.
set -euo pipefail

: "${JARI_MODELS_DIR:?Set JARI_MODELS_DIR}"
: "${JARI_RESULTS_DIR:?Set JARI_RESULTS_DIR}"
: "${DOCKQ_EXECUTABLE:?Set DOCKQ_EXECUTABLE}"

# Some Triton compute nodes do not mount the /projectnb/triton path alias.
# /nethome/$USER is visible on those nodes and refers to the same user files.
repo_source=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
compute_home="/nethome/${USER:?USER is not set}"
repo_root="$compute_home/$(basename "$repo_source")"
[[ -d "$repo_root" ]] || { echo "Compute-visible repository not found: $repo_root" >&2; exit 1; }
python_executable=${PYTHON_EXECUTABLE:-"$repo_root/.venv/bin/python"}
[[ -x "$python_executable" ]] || { echo "Python executable not found: $python_executable" >&2; exit 2; }
manifest="$JARI_MODELS_DIR/model_manifest.txt"
[[ -s "$manifest" ]] || { echo "Missing $manifest" >&2; exit 1; }

queue=${LSF_QUEUE:-normal}
walltime=${LSF_WALLTIME:-240:00}
resource_requirement=${LSF_RESOURCE_REQUIREMENT:-'select[hname!=t082] span[hosts=1]'}
workers=${DOCKQ_WORKERS:-1}
[[ "$workers" =~ ^[1-9][0-9]*$ ]] || { echo "DOCKQ_WORKERS must be a positive integer." >&2; exit 2; }
exclusive_flag=()
if [[ ${LSF_EXCLUSIVE_NODE:-0} == 1 ]]; then
  exclusive_flag=(-x)
fi
resume_flag=(--resume)
if [[ ${JARI_RESUME:-1} == 0 ]]; then
  resume_flag=()
fi
cross_mode=${JARI_CROSS_MODE:-model}
[[ "$cross_mode" == model || "$cross_mode" == pair ]] || {
  echo "JARI_CROSS_MODE must be model or pair." >&2
  exit 2
}
mkdir -p "$JARI_RESULTS_DIR/logs"

while IFS= read -r model_name; do
  if [[ "$cross_mode" == model ]]; then
    bsub -q "$queue" -W "$walltime" -n "$workers" "${exclusive_flag[@]}" -R "$resource_requirement" -J "jari_cross_${model_name}" \
      -oo "$JARI_RESULTS_DIR/logs/cross.${model_name}.%J.out" \
      -eo "$JARI_RESULTS_DIR/logs/cross.${model_name}.%J.err" \
      "$python_executable" "$repo_root/scripts/02_run_cross_dockq.py" "$JARI_MODELS_DIR" \
        --model-name "$model_name" --dockq-executable "$DOCKQ_EXECUTABLE" \
        --output-dir "$JARI_RESULTS_DIR/cross_scores" --processes 1 \
        --comparison-workers "$workers" --mapping AB:AB "${resume_flag[@]}"
  else
    while IFS= read -r other_model_name; do
      [[ "$other_model_name" == "$model_name" ]] && continue
      bsub -q "$queue" -W "$walltime" -n "$workers" "${exclusive_flag[@]}" -R "$resource_requirement" -J "jari_cross_${model_name}_to_${other_model_name}" \
        -oo "$JARI_RESULTS_DIR/logs/cross.${model_name}_to_${other_model_name}.%J.out" \
        -eo "$JARI_RESULTS_DIR/logs/cross.${model_name}_to_${other_model_name}.%J.err" \
        "$python_executable" "$repo_root/scripts/02_run_cross_dockq.py" "$JARI_MODELS_DIR" \
          --model-name "$model_name" --other-model-name "$other_model_name" \
          --dockq-executable "$DOCKQ_EXECUTABLE" --output-dir "$JARI_RESULTS_DIR/cross_scores" \
          --processes 1 --comparison-workers "$workers" --mapping AB:AB "${resume_flag[@]}"
    done < "$manifest"
  fi
  bsub -q "$queue" -W "$walltime" -n "$workers" "${exclusive_flag[@]}" -R "$resource_requirement" -J "jari_self_${model_name}" \
    -oo "$JARI_RESULTS_DIR/logs/self.${model_name}.%J.out" \
    -eo "$JARI_RESULTS_DIR/logs/self.${model_name}.%J.err" \
    "$python_executable" "$repo_root/scripts/03_run_self_dockq.py" "$JARI_MODELS_DIR" \
      --model-name "$model_name" --dockq-executable "$DOCKQ_EXECUTABLE" \
      --output-dir "$JARI_RESULTS_DIR/self_scores" --processes 1 \
      --comparison-workers "$workers" --mapping AB:AB "${resume_flag[@]}"
done < "$manifest"
