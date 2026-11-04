# Highway Energy System

Code and supporting data for highway service-area energy-system research, combining multi-objective optimization with XGBoost and SHAP analysis.

## Repository structure

```text
Highway-Energy-System/
├── README.md
├── data/
│   ├── README.md
│   └── data2/                 # Original supporting-data organization
├── optimization/
│   ├── README.md
│   ├── requirements.txt
│   └── main.py
└── xgboost-shap/
    ├── README.md
    ├── requirements.txt
    └── XGBoost+SHAP.py
```

## Modules

- [Optimization](optimization/README.md): Pyomo/Gurobi multi-objective optimization of cost and carbon emissions.
- [XGBoost and SHAP](xgboost-shap/README.md): regression modeling and interpretation.
- [Supporting data](data/README.md): original Excel inputs and dataset descriptions.

## Installation and execution

Use separate Python environments for the two modules because their pinned dependencies differ. Run the commands below from the repository root. On Windows use `py -3.11` or `py -3.9`; on other systems use the corresponding Python executable and environment activation command.

### Optimization (Python 3.11)

```powershell
py -3.11 -m venv .venv-optimization
.venv-optimization\Scripts\python.exe -m pip install -r optimization/requirements.txt
# Configure optimization/config.py and prepare the required input tables first.
.venv-optimization\Scripts\python.exe optimization/main.py
```

A valid Gurobi installation and license are required. Configure the four input paths, `co2_grid_factor`, and `price_sell` in `optimization/config.py`. Default input placeholders point to `data/processed/`; optimization results are written to `results/optimization/`. These paths are resolved relative to this repository, regardless of the current working directory.

### XGBoost and SHAP (Python 3.9)

```powershell
py -3.9 -m venv .venv-xgboost-shap
.venv-xgboost-shap\Scripts\python.exe -m pip install -r xgboost-shap/requirements.txt
# Configure csv_file_path and target_column_name in the script first.
.venv-xgboost-shap\Scripts\python.exe xgboost-shap/XGBoost+SHAP.py
```

The default input placeholder is `data/processed/your_shap_data.csv`. CSV and Excel input are supported. Figure outputs follow the script's existing conventions and are created relative to the current working directory.

## Data and reproducibility

The supplied `data/data2/` directory preserves the original supporting dataset. It is not automatically mapped to the model's four input tables or to an XGBoost training table. See [data requirements and current scope](data/README.md) before running either module.

The conceptual workflow is supporting data → preparation of model-ready tables → optimization → assembly of feature/target tables → XGBoost and SHAP analysis. An automated end-to-end data-preparation pipeline is not included. Full model execution still requires compatible inputs and project-specific parameter values.

## Project origins

This is a new consolidated repository. The existing standalone repositories remain separate and unchanged:

- [Highway-Optimization](https://github.com/Haoyu-0621/Highway-Optimization)
- [Highway-XGBoost-SHAP](https://github.com/Haoyu-0621/Highway-XGBoost-SHAP)

Each module retains its original README and dependency file, with integration-specific path notes. The original repositories' Git histories are not imported into this repository.
