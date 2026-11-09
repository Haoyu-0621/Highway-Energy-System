# Highway Energy System

Code and supporting data for highway service-area energy-system research, combining multi-objective optimization with XGBoost and SHAP analysis.

## Repository structure

```text
Highway-Energy-System/
├── README.md
├── requirements.txt          # Reading the supplied CSV/Excel data (Python 3.11)
├── data/
│   ├── README.md
│   ├── data1/
│   │   └── service_area_data.csv  # Annual summary for 3,094 service areas
│   └── data2/                 # Seven regional typical sites and supporting tables
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

### Data requirements and dependencies

`data/data1/service_area_data.csv` contains one annual summary record for each of **3,094 highway service areas**. Fields include longitude, latitude, province, region, PV installation area, PV installed capacity, annual PV generation, annual building electricity consumption, annual EV charging electricity consumption, and annual tunnel electricity consumption. The [data dictionary](data/README.md) lists exact column names and units.

The **8760-hour profiles in `data/data2/` cover seven selected typical service areas, one from each of China's seven major regions**. Each selected site has 8,760 hourly observations at **1-hour resolution**, representing 365 × 24 hours. The hourly PV generation, building load, and EV charging workbooks share these seven sites. The directory also includes tunnel information and separate 24-hour load tables. See the [site mapping and workbook layout](data/README.md).

To read the supplied CSV and Excel files with Python 3.11, install the root data-reading requirements. Run from the repository root.

```powershell
py -3.11 -m venv codex工作文件/.venv-data
codex工作文件/.venv-data/Scripts/python.exe -m pip install -r requirements.txt
```

The root `requirements.txt` pins pandas and openpyxl for data reading. Module-specific dependency files below define the optimization and XGBoost/SHAP environments. Gurobi also requires a valid license.

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

The supplied data includes the annual summary for 3,094 service areas in `data/data1/` and the seven regional typical-site hourly profiles with supporting tables in `data/data2/`. Model execution requires an explicit mapping from these source tables to the four configured optimization inputs or to an XGBoost feature/target table. See [data requirements and current scope](data/README.md) before running either module.

The conceptual workflow is supporting data → preparation of model-ready tables → optimization → assembly of feature/target tables → XGBoost and SHAP analysis. An automated end-to-end data-preparation pipeline is not included. Full model execution still requires compatible inputs and project-specific parameter values.

## Project origins

This is a new consolidated repository. The existing standalone repositories remain separate and unchanged:

- [Highway-Optimization](https://github.com/Haoyu-0621/Highway-Optimization)
- [Highway-XGBoost-SHAP](https://github.com/Haoyu-0621/Highway-XGBoost-SHAP)

Each module retains its original README and dependency file, with integration-specific path notes. The original repositories' Git histories are not imported into this repository.
