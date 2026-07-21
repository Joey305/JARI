# JARI-PROTACS

Reproducible scripts for processing PyRosettaC outputs, calculating DockQ similarity scores, and clustering ligands or model poses using pairwise structural similarity.

This repository reorganizes a legacy internal workflow into a chronological pipeline that is easier to run, document, and share on GitHub.

## What This Repo Does

The workflow is built around PyRosettaC output folders that contain model directories with `cluster*` subfolders and PDB files inside each cluster.

At a high level, the pipeline:

1. prepares PDB files for DockQ scoring
2. runs cross-model and self-model DockQ comparisons
3. exports raw text reports into Excel workbooks
4. merges those workbooks into a single tabular dataset
5. averages pairwise DockQ scores across unordered model-PDB pairs
6. clusters models using DBSCAN or hierarchical clustering
7. optionally remaps model and PDB names to coded legends

## Repository Layout

```text
scripts/
  01_prepare_pdbs_for_dockq.py
  02_run_cross_dockq.py
  03_run_self_dockq.py
  04_export_cross_scores_to_excel.py
  05_export_self_scores_to_excel.py
  06_merge_score_workbooks.py
  07_average_pairwise_dockq.py
  08_apply_model_code_legend.py
  09_apply_pdb_code_legend.py
  10_fix_shifted_coded_rows.py
  11_cluster_dbscan_umap.py
  12_plot_dendrogram.py
archive/
  legacy/
  experimental/
```

`scripts/` contains the primary cleaned pipeline.  
`archive/` contains older helper scripts and experiments preserved for reference.

## Expected Input Structure

The DockQ-running scripts expect something like:

```text
your_models/
  model_a/
    cluster1/
      combined_001.pdb
      combined_002.pdb
    cluster2/
      combined_003.pdb
  model_b/
    cluster1/
      combined_001.pdb
```

## Requirements

- Python 3.10+
- [DockQ](https://github.com/bjornwallner/DockQ)
- Python packages from [requirements.txt](/Users/jxs794/Documents/JARI-PROTACS/requirements.txt)

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Recommended Workflow

### 1. Prepare PDB files

```bash
python scripts/01_prepare_pdbs_for_dockq.py /path/to/your_models
```

### 2. Run DockQ comparisons across different models

```bash
python scripts/02_run_cross_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py
```

Outputs are written to `results/cross_scores/`.

### 3. Run DockQ comparisons within each model

```bash
python scripts/03_run_self_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py
```

Outputs are written to `results/self_scores/`.

### 4. Convert text reports into workbooks

```bash
python scripts/04_export_cross_scores_to_excel.py results/cross_scores
python scripts/05_export_self_scores_to_excel.py results/self_scores
```

Outputs are written to `results/workbooks/`.

### 5. Merge workbooks into one combined CSV

```bash
python scripts/06_merge_score_workbooks.py \
  results/workbooks/self_scores.xlsx \
  results/workbooks/cross_scores.xlsx
```

Output:

- `results/tables/all_data_combined.csv`

### 6. Average pairwise DockQ scores

```bash
python scripts/07_average_pairwise_dockq.py results/tables/all_data_combined.csv
```

Outputs:

- `results/tables/averaged_dockq_scores.csv`
- `results/tables/unpaired_entries.csv`

### 7. Cluster models with DBSCAN and visualize with UMAP

```bash
python scripts/11_cluster_dbscan_umap.py results/tables/averaged_dockq_scores.csv
```

Outputs:

- `results/clustering/dbscan_cluster_assignments.csv`
- `results/clustering/dbscan_umap.png`

### 8. Plot hierarchical clustering dendrograms

```bash
python scripts/12_plot_dendrogram.py results/tables/averaged_dockq_scores.csv
```

Outputs:

- `results/clustering/dendrogram_full.png`
- `results/clustering/dendrogram_truncated.png`

## Optional Legend/Coding Steps

If your project uses coded ligand or model names:

```bash
python scripts/08_apply_model_code_legend.py path/to/Model_PDB_Legend_Mapping.xlsx results/tables/all_data_combined.csv
python scripts/09_apply_pdb_code_legend.py path/to/NEW_Model_PDB_Legend_Mapping_PDBCODE.xlsx results/tables/coded1_all_data_combined.csv
python scripts/10_fix_shifted_coded_rows.py results/tables/coded2_all_data_combined.csv
```

## Notes

- The workflow assumes DockQ output contains parseable `DockQ`, `iRMS`, and `LRMS` values.
- The current clustering scripts use `1 - Average_DockQ` as a distance metric.
- Some older archived scripts were clearly prototype-stage and may require manual inspection before reuse.

## Status

This repository cleanup was completed on July 20, 2026, by reorganizing the historical project files into a cleaner numbered pipeline for public-facing use.
