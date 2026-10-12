#!/usr/bin/env bash
# Compute-node-safe DockQ launcher for Triton.
# The pip-installed DockQ script has a shebang tied to the /projectnb path
# alias, which is unavailable on some compute nodes. Invoke it explicitly
# through the /nethome-visible virtual-environment Python instead.
set -euo pipefail

script_path=$(readlink -f "${BASH_SOURCE[0]}")
repo_root=$(cd "$(dirname "$script_path")/../.." && pwd)
exec "$repo_root/.venv/bin/python" "$repo_root/.venv/bin/DockQ" "$@"
