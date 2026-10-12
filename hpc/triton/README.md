# Triton / LSF DockQ execution

## Recommended generic launcher

For a directory of PRosettaC result ZIPs, use `jari-run`. It creates a stable
short-name manifest, stages archives once, and submits resumable jobs. There
are two cross-comparison modes:

| Command | Cross-job granularity | Best for |
| --- | --- | --- |
| `jari-run ZIP_DIRECTORY --name RUN` | One model against every other model | Fewer jobs and standard production runs |
| `jari-run-single ZIP_DIRECTORY --name RUN` | One directed model-to-model (1×1) comparison per job | Fine-grained scheduling, recovery, and progress tracking |

Directed 1×1 mode creates jobs for both orientations of every pair (A→B and
B→A), because the downstream pipeline records directed score reports before
averaging unordered pairs. Both commands submit one self-comparison job per
model. Use `--queue` and `--walltime` to match the local LSF policy.

```bash
cd /path/to/JARI-PROTACS
hpc/triton/jari-run /path/to/result-zips --name standard-run
hpc/triton/jari-run-single /path/to/result-zips --name directed-pairs
```

The scripts assume a Triton-visible repository clone at `/nethome/$USER/<repo>`
and a project virtual environment at `.venv`. Adjust the scripts if your site
uses a different compute-visible path.

## Legacy Pomalidomide workflow

This setup uses two LSF job arrays, each with one task per Pomalidomide model:

| Array | Tasks | Work per task |
| --- | ---: | --- |
| `poma_cross` | 23 | One model against each of the other 22 models |
| `poma_self` | 23 | All within-model PDB comparisons |

That is **46 LSF tasks**, not 46 copies of the whole pipeline. `02_run_cross_dockq.py` intentionally records both orientations of a cross-model pair (A→B and B→A), matching the existing pipeline and its downstream averaging. Each array task receives one PROTAC and scores it against every other PROTAC. By default each task requests one core; set `DOCKQ_WORKERS` only after validating a multi-core LSF configuration.

## 1. Copy the project and archives

From the local Mac (replace `NETID` and the Triton destination):

```bash
rsync -av --progress \
  --exclude '.git' --exclude '__pycache__' --exclude 'results' \
  /path/to/JARI-PROTACS/ NETID@triton.example.edu:~/projects/JARI-PROTACS/
```

The source archives are already at `Pomalidomide-Structures/*_Results.zip`; do not unzip them all into one directory because every archive contains a directory called `Results`.

## 2. Create a Triton Python environment and install DockQ

On Triton, use the module/version required by your site (the command below uses a common Python module name):

```bash
cd ~/projects/JARI-PROTACS
module load python/3.11
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt DockQ
export DOCKQ_EXECUTABLE="$(command -v DockQ)"
DockQ --help
```

If your approved DockQ installation is a cloned directory instead, set `DOCKQ_EXECUTABLE` to its executable file, for example `~/software/DockQ/DockQ.py`, and make it executable with `chmod u+x`. Adding the directory to `PATH` is fine, but the array scripts use the explicit executable path so the jobs are reproducible.

## 3. Expand the raw model archives once

Use the PRosettaC PDBs **unchanged** with DockQ v2. The archived structures have protein chains `A` and `B`, plus the PROTAC/linker as `HETATM` chain `X`. DockQ v2 automatically maps chains; keeping `X` distinct also agrees with its small-molecule design. Do not run the legacy `01_prepare_pdbs_for_dockq.py` unless a controlled comparison shows that it is required for a specific older DockQ version.

```bash
cd ~/projects/JARI-PROTACS
source .venv/bin/activate
export POMA_MODELS_DIR="$PWD/work/pomalidomide_models"
export POMA_RESULTS_DIR="$PWD/results/pomalidomide"
export DOCKQ_EXECUTABLE="$(command -v DockQ)"

bash hpc/triton/prepare_pomalidomide_models.sh \
  "$PWD/Pomalidomide-Structures" "$POMA_MODELS_DIR"
```

This creates 23 separate raw model directories and a fixed `model_manifest.txt`. The fixed manifest keeps LSF array indexes stable.

## 4. Preflight one unedited DockQ comparison

```bash
mapfile -t test_pdbs < <(find "$POMA_MODELS_DIR" -name 'combined*.pdb' -print | head -n 2)
"$DOCKQ_EXECUTABLE" "${test_pdbs[0]}" "${test_pdbs[1]}" --mapping AB:AB
```

Confirm that the output includes `DockQ`, `iRMS`, and `LRMS`. `--mapping AB:AB` is a useful diagnostic to explicitly score the protein-protein interface; the production scripts use DockQ v2's automatic mapping. Then test one scheduler task before the full submission:

```bash
export LSB_JOBINDEX=1
bash hpc/triton/run_pomalidomide_self_array.sh
unset LSB_JOBINDEX
```

Remove `"$POMA_RESULTS_DIR/self_scores/${first_model}_self_scores.txt"` after this local test, since the LSF task will regenerate it.

## 5. Submit and monitor

```bash
unset LSB_JOBINDEX
# Triton's current general-purpose CPU queue is normal.
export LSF_QUEUE=normal
bash hpc/triton/submit_pomalidomide_arrays.sh

bjobs -w
bhist -l <job-id>
```

The submission script emits two LSF job IDs. Outputs are independent, one file per task, under `results/pomalidomide/cross_scores` and `results/pomalidomide/self_scores`; logs are in `results/pomalidomide/logs`. After both arrays finish successfully, continue locally or on Triton with steps 4–7 of the standard pipeline.

Before submitting, verify Triton's exact `module load` command, queue name, wall-time policy, and whether compute nodes can access the project filesystem. Those settings are site-specific and cannot be inferred from this repository.
