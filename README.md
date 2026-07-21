# 🧪 JARI-PROTACS

<p align="center">
  <strong>JARI-PROTACS: A reproducible PyRosettaC-to-DockQ ligand clustering workflow</strong>
</p>

<p align="center">
  <em>Structured scripts for preparing PyRosettaC outputs, computing pairwise DockQ similarity, and organizing ligand or pose clusters with DBSCAN and hierarchical clustering.</em>
</p>

<p align="center">
  <a href="#quick-start">
    <img src="https://img.shields.io/badge/Get%20Started-Quick%20Start-blue?style=for-the-badge&logo=python" alt="Quick start">
  </a>
  <a href="#workflow-overview">
    <img src="https://img.shields.io/badge/Workflow-Pipeline%20Overview-orange?style=for-the-badge&logo=githubactions" alt="Workflow overview">
  </a>
  <a href="#repository-layout">
    <img src="https://img.shields.io/badge/Repo-Directory%20Layout-lightgrey?style=for-the-badge&logo=files" alt="Repository layout">
  </a>
  <a href="#clustering-outputs">
    <img src="https://img.shields.io/badge/Outputs-Clustering%20Artifacts-success?style=for-the-badge&logo=databricks" alt="Clustering outputs">
  </a>
</p>

<p align="center">
  <a href="https://github.com/bjornwallner/DockQ">
    <img src="https://img.shields.io/badge/Dependency-DockQ-informational?style=for-the-badge&logo=python" alt="DockQ dependency">
  </a>
  <a href="./requirements.txt">
    <img src="https://img.shields.io/badge/Python-Requirements-green?style=for-the-badge&logo=pypi" alt="Python requirements">
  </a>
  <a href="./scripts">
    <img src="https://img.shields.io/badge/Scripts-Numbered%20Pipeline-purple?style=for-the-badge&logo=gnubash" alt="Numbered pipeline">
  </a>
</p>

---

<a id="overview"></a>

## 🚀 Overview

**JARI-PROTACS** is a cleaned and reorganized analysis repository for processing **PyRosettaC** results into a reproducible **DockQ-based clustering workflow**.

The project is designed for cases where you want to:

- prepare PyRosettaC-generated PDBs for DockQ compatibility
- compare model clusters across ligands or linker designs
- compute pairwise DockQ, iRMS, and LRMS values
- aggregate those comparisons into a unified dataset
- average pairwise structural similarity scores
- cluster ligands or poses using **DBSCAN**
- visualize structural grouping with **UMAP** and **hierarchical dendrograms**

This repository began as a long-running internal project with several legacy scripts from different development phases. It has now been reorganized into a chronological pipeline intended to be easier to understand, run, and share publicly.

---

<a id="repository-navigation"></a>

## 🧭 Repository Navigation

<p align="center">
  <a href="#quick-start">
    <img src="https://img.shields.io/badge/Start-Quick%20Start-yellow?style=for-the-badge&logo=gnubash" alt="Quick start">
  </a>
  <a href="#workflow-overview">
    <img src="https://img.shields.io/badge/Read-Pipeline%20Overview-blue?style=for-the-badge&logo=readthedocs" alt="Pipeline overview">
  </a>
  <a href="#repository-layout">
    <img src="https://img.shields.io/badge/Browse-Repo%20Layout-lightgrey?style=for-the-badge&logo=github" alt="Repo layout">
  </a>
  <a href="#requirements">
    <img src="https://img.shields.io/badge/Install-Requirements-success?style=for-the-badge&logo=pypi" alt="Requirements">
  </a>
  <a href="#optional-coding-and-legend-steps">
    <img src="https://img.shields.io/badge/Optional-Legend%20Mapping-orange?style=for-the-badge&logo=microsoftexcel" alt="Legend mapping">
  </a>
</p>

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Workflow Overview](#workflow-overview)
- [Repository Layout](#repository-layout)
- [Expected Input Structure](#expected-input-structure)
- [Requirements](#requirements)
- [Core Pipeline](#core-pipeline)
- [Clustering Outputs](#clustering-outputs)
- [Optional Coding and Legend Steps](#optional-coding-and-legend-steps)
- [Archived Material](#archived-material)
- [Status](#status)

---

<a id="quick-start"></a>

## ⚡ Quick Start

If you already have a folder of PyRosettaC model outputs and a working DockQ installation, the shortest path through the workflow is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/01_prepare_pdbs_for_dockq.py /path/to/your_models
python scripts/02_run_cross_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py
python scripts/03_run_self_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py

python scripts/04_export_cross_scores_to_excel.py results/cross_scores
python scripts/05_export_self_scores_to_excel.py results/self_scores
python scripts/06_merge_score_workbooks.py results/workbooks/self_scores.xlsx results/workbooks/cross_scores.xlsx
python scripts/07_average_pairwise_dockq.py results/tables/all_data_combined.csv

python scripts/11_cluster_dbscan_umap.py results/tables/averaged_dockq_scores.csv
python scripts/12_plot_dendrogram.py results/tables/averaged_dockq_scores.csv
```

That sequence will take you from prepared PDB files to merged scoring tables and final clustering figures.

---

<a id="workflow-overview"></a>

## 🔬 Workflow Overview

The repository is organized as a numbered pipeline so the execution order is explicit.

| Stage | Script | Purpose |
|---|---|---|
| 01 | `01_prepare_pdbs_for_dockq.py` | Adjust chain and residue formatting so PyRosettaC outputs are DockQ-compatible |
| 02 | `02_run_cross_dockq.py` | Compare models across different folders or ligand/linker conditions |
| 03 | `03_run_self_dockq.py` | Compare models within the same folder for self-similarity scoring |
| 04 | `04_export_cross_scores_to_excel.py` | Convert cross-model text reports into a workbook |
| 05 | `05_export_self_scores_to_excel.py` | Convert self-score text reports into a workbook |
| 06 | `06_merge_score_workbooks.py` | Merge workbook sheets into one combined table |
| 07 | `07_average_pairwise_dockq.py` | Average unordered model-PDB pair scores |
| 08 | `08_apply_model_code_legend.py` | Replace model names with legend codes |
| 09 | `09_apply_pdb_code_legend.py` | Collapse model/PDB combinations into compact coded identifiers |
| 10 | `10_fix_shifted_coded_rows.py` | Repair left-shifted coded CSV rows when needed |
| 11 | `11_cluster_dbscan_umap.py` | Cluster structures with DBSCAN and visualize with UMAP |
| 12 | `12_plot_dendrogram.py` | Generate hierarchical clustering dendrograms |

The main structural metric used downstream is:

`distance = 1 - Average_DockQ`

This allows higher DockQ similarity to correspond to shorter clustering distance.

---

<a id="repository-layout"></a>

## 📦 Repository Layout

```text
JARI-PROTACS/
├── README.md
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── 01_prepare_pdbs_for_dockq.py
│   ├── 02_run_cross_dockq.py
│   ├── 03_run_self_dockq.py
│   ├── 04_export_cross_scores_to_excel.py
│   ├── 05_export_self_scores_to_excel.py
│   ├── 06_merge_score_workbooks.py
│   ├── 07_average_pairwise_dockq.py
│   ├── 08_apply_model_code_legend.py
│   ├── 09_apply_pdb_code_legend.py
│   ├── 10_fix_shifted_coded_rows.py
│   ├── 11_cluster_dbscan_umap.py
│   └── 12_plot_dendrogram.py
└── archive/
    ├── legacy/
    └── experimental/
```

`scripts/` contains the cleaned public-facing workflow.  
`archive/` preserves older helper scripts and prototype analyses that were retained for reference but are not part of the recommended primary run path.

---

<a id="expected-input-structure"></a>

## 🧱 Expected Input Structure

The DockQ execution scripts expect model folders with `cluster*` subdirectories containing PDB files:

```text
your_models/
├── model_a/
│   ├── cluster1/
│   │   ├── combined_001.pdb
│   │   └── combined_002.pdb
│   └── cluster2/
│       └── combined_003.pdb
├── model_b/
│   └── cluster1/
│       └── combined_001.pdb
└── model_c/
    ├── cluster1/
    └── cluster2/
```

In practical terms:

- each top-level model folder usually corresponds to a ligand, linker, design, or pose family
- each `cluster*` folder represents a PyRosettaC cluster
- each PDB inside a cluster is used for pairwise DockQ scoring

---

<a id="requirements"></a>

## ⚙️ Requirements

- Python 3.10+
- [DockQ](https://github.com/bjornwallner/DockQ)
- packages listed in [requirements.txt](./requirements.txt)

Install the Python dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The clustering and visualization steps rely on:

- `pandas`
- `numpy`
- `scipy`
- `scikit-learn`
- `umap-learn`
- `matplotlib`
- `openpyxl`
- `xlsxwriter`

---

<a id="core-pipeline"></a>

## 🧬 Core Pipeline

### 1. Prepare DockQ-compatible PDBs

```bash
python scripts/01_prepare_pdbs_for_dockq.py /path/to/your_models
```

This step updates chain/residue formatting so the downstream DockQ comparisons behave consistently.

### 2. Run cross-model DockQ scoring

```bash
python scripts/02_run_cross_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py
```

Output directory:

- `results/cross_scores/`

### 3. Run self-model DockQ scoring

```bash
python scripts/03_run_self_dockq.py /path/to/your_models --dockq-executable /path/to/DockQ.py
```

Output directory:

- `results/self_scores/`

### 4. Convert raw score text files into workbooks

```bash
python scripts/04_export_cross_scores_to_excel.py results/cross_scores
python scripts/05_export_self_scores_to_excel.py results/self_scores
```

Output directory:

- `results/workbooks/`

### 5. Merge workbooks into one combined score table

```bash
python scripts/06_merge_score_workbooks.py \
  results/workbooks/self_scores.xlsx \
  results/workbooks/cross_scores.xlsx
```

Primary output:

- `results/tables/all_data_combined.csv`

### 6. Average unordered pairwise DockQ scores

```bash
python scripts/07_average_pairwise_dockq.py results/tables/all_data_combined.csv
```

Outputs:

- `results/tables/averaged_dockq_scores.csv`
- `results/tables/unpaired_entries.csv`

### 7. Run clustering and visualization

```bash
python scripts/11_cluster_dbscan_umap.py results/tables/averaged_dockq_scores.csv
python scripts/12_plot_dendrogram.py results/tables/averaged_dockq_scores.csv
```

Outputs:

- `results/clustering/dbscan_cluster_assignments.csv`
- `results/clustering/dbscan_umap.png`
- `results/clustering/dendrogram_full.png`
- `results/clustering/dendrogram_truncated.png`

---

<a id="clustering-outputs"></a>

## 📊 Clustering Outputs

After the workflow is complete, the main analysis artifacts are:

- pairwise averaged DockQ score tables
- DBSCAN cluster assignments
- UMAP scatterplots for cluster structure
- full and truncated hierarchical dendrograms

These outputs are intended to support ligand-family inspection, linker comparison, and pose similarity interpretation across PyRosettaC result sets.

---

<a id="optional-coding-and-legend-steps"></a>

## 🏷️ Optional Coding and Legend Steps

Some historical runs used coded model or PDB identifiers for cleaner downstream labeling. Those steps are still available when needed.

### Replace model names with legend codes

```bash
python scripts/08_apply_model_code_legend.py \
  path/to/Model_PDB_Legend_Mapping.xlsx \
  results/tables/all_data_combined.csv
```

### Convert model/PDB pairs into compact coded identifiers

```bash
python scripts/09_apply_pdb_code_legend.py \
  path/to/NEW_Model_PDB_Legend_Mapping_PDBCODE.xlsx \
  results/tables/coded1_all_data_combined.csv
```

### Repair shifted coded CSV rows if needed

```bash
python scripts/10_fix_shifted_coded_rows.py results/tables/coded2_all_data_combined.csv
```

These steps are optional and mainly useful if your project already depends on a legacy naming legend or compact coded labels for figures and spreadsheets.

---

<a id="archived-material"></a>

## 🗃️ Archived Material

The `archive/` folder is intentionally kept in the repository.

- `archive/legacy/` contains older support scripts that were part of earlier workbook-based processing
- `archive/experimental/` contains prototype clustering or parameter-sweep material that informed the cleaned workflow

These files are preserved for provenance and internal continuity, but they are not the recommended entry point for new users.

---

<a id="status"></a>

## 📌 Status

This repository was reorganized on **July 20, 2026** into a numbered, cleaner pipeline intended for public GitHub use.

Current state:

- the core scripts are renamed in chronological order
- the README and repository layout are now public-facing
- the cleaned scripts compile successfully
- full end-to-end execution still depends on real PyRosettaC input folders and an available DockQ installation

---

## Contact

For workflow questions, repository cleanup follow-up, or collaboration around PyRosettaC-based ligand clustering, update this section with the preferred lab or project contact before broad public release.
