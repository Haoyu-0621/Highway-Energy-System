# XGBoost + SHAP Analysis

XGBoost regression and SHAP interpretation for analyzing the relationships between highway service-area characteristics and selected energy-system indicators.

## Features

- CSV and Excel data input.
- Log transformation of the target variable with offset handling.
- Numeric conversion and categorical feature encoding.
- Hyperparameter tuning through grid search and cross-validation.
- Model evaluation on the original target scale.
- Feature importance, SHAP summary, dependence, and interaction analysis.

## Project Structure

```text
xgboost-shap/
├── XGBoost+SHAP.py  # Data preparation, regression, and SHAP analysis
├── requirements.txt
└── README.md
```

## Requirements

Python 3.9 is used for this module. Dependencies include XGBoost, SHAP, scikit-learn, pandas, NumPy, Matplotlib, seaborn, SciPy, statsmodels, and openpyxl. Library versions are listed in [requirements.txt](requirements.txt).

From the repository root, install the module dependencies in its Python environment.

```bash
python -m pip install -r xgboost-shap/requirements.txt
```

## Data Requirements

Use a CSV or Excel table containing the explanatory variables and a numeric target selected for the research question. Set the input file and target column in the script.

The [annual service-area dataset](../data/data1/service_area_data.csv) provides geographical, PV, and annual electricity variables for 3,094 service areas. For analyses of optimized cost or carbon emissions, combine the corresponding optimization results with the selected site characteristics.
