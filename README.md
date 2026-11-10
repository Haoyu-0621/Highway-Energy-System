# Highway Energy System

Code and supporting data for highway service-area energy-system research, combining multi-objective PV and battery storage optimization with XGBoost regression and SHAP interpretation.

## Repository Structure

```text
Highway-Energy-System/
├── README.md
├── requirements.txt       # Data-reading dependencies
├── data/
│   ├── README.md
│   ├── data1/             # Annual summary for 3,094 service areas
│   └── data2/             # Seven typical sites and supporting data
├── optimization/          # Multi-objective energy-system optimization
└── xgboost-shap/           # Regression and model interpretation
```

## Modules

- **Optimization** — Pyomo/Gurobi planning of PV and battery storage systems, with Pareto analysis of annual cost and carbon emissions. See the [module description and data requirements](optimization/README.md).
- **XGBoost and SHAP** — regression modeling, feature importance, and interpretation of relationships between service-area characteristics and selected energy-system indicators. See the [module description](xgboost-shap/README.md).

## Data

`data/data1/service_area_data.csv` contains **3,094 annual service-area records**, including longitude, latitude, province, region, PV installation area, installed PV capacity, annual PV generation, and annual building, EV charging, and tunnel electricity consumption.

`data/data1/tunnel_data.csv` contains **6,243 tunnel records** with tunnel lengths, provinces, associated facilities, and distances to those facilities, using English labels and romanized place names.

The hourly profiles in `data/data2/` cover **seven selected typical service areas, one from each of China's seven major regions**. Each typical site has **8,760 observations at 1-hour resolution** for PV generation, building load, and EV charging load. The directory also includes site and PV installation areas, tunnel attributes, and supporting 24-hour load profiles.

See the [data description](data/README.md) for field units, typical-site names, and file contents.

## Requirements

Use separate Python environments for the two analysis modules because their library versions differ.

- **Data reading** — Python 3.11, pandas, and openpyxl. Install from the root [requirements.txt](requirements.txt).
- **Optimization** — Python 3.11, Pyomo, Gurobi, and the libraries in [optimization/requirements.txt](optimization/requirements.txt). A valid Gurobi license is required. Set the regional grid carbon emission factor and electricity sale price in `optimization/config.py`.
- **XGBoost and SHAP** — Python 3.9 and the libraries in [xgboost-shap/requirements.txt](xgboost-shap/requirements.txt).

Install the appropriate dependency file in the selected environment with `python -m pip install -r <requirements-file>`.
