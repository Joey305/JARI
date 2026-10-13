#!/usr/bin/env bash
# Run a dependency-free check of the core DockQ job orchestration.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/jari-protacs-smoke.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT

mkdir -p "$work_dir/models/model_a/cluster1" "$work_dir/models/model_b/cluster1"
touch "$work_dir/models/model_a/cluster1/combined_001.pdb"
touch "$work_dir/models/model_a/cluster1/combined_002.pdb"
touch "$work_dir/models/model_b/cluster1/combined_003.pdb"

python3 "$repo_root/scripts/03_run_self_dockq.py" "$work_dir/models" \
  --dockq-executable "$repo_root/tests/fake_dockq.py" \
  --output-dir "$work_dir/self" --processes 1 --comparison-workers 1

python3 "$repo_root/scripts/02_run_cross_dockq.py" "$work_dir/models" \
  --model-name model_a --other-model-name model_b \
  --dockq-executable "$repo_root/tests/fake_dockq.py" \
  --output-dir "$work_dir/cross" --processes 1 --comparison-workers 1

test -s "$work_dir/self/model_a_self_scores.txt"
test -s "$work_dir/cross/model_a__vs__model_b_dockq_high_scores.txt"
grep -q $'DockQ\tiRMS\tLRMS' "$work_dir/self/model_a_self_scores.txt"
grep -q $'model_a\tcluster1\tcombined_001.pdb\tmodel_b' "$work_dir/cross/model_a__vs__model_b_dockq_high_scores.txt"

echo "JARI-PROTACS smoke test passed."
