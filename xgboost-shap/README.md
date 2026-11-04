> Consolidated repository: see the [main README](../README.md) and [shared data notes](../data/README.md). This module has its own Python environment. Input paths are resolved relative to the repository through `REPOSITORY_ROOT`; edit the placeholders before running.

# XGBoost + SHAP Analysis

This repository contains a Python script for training an XGBoost regression model and interpreting the model with SHAP.

## Features

- Loads data from a CSV or Excel file
- Applies a log transform to the target variable with automatic offset handling
- Processes non-numeric features before training
- Tunes the XGBoost model with grid search and cross-validation
- Reports model performance on the original target scale
- Generates feature-importance plots
- Generates SHAP summary and dependence plots

## Project Structure

- `XGBoost+SHAP.py`: main analysis script
- `requirements.txt`: Python dependencies with pinned versions

## Environment

- Python 3.9

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Open `XGBoost+SHAP.py` and update the user configuration section:

- `csv_file_path`: set this to your dataset path
- `target_column_name`: set this to your regression target column
- `sheet_name`: set this only when using an Excel file

Example:

```python
csv_file_path = r"path/to/your/data.csv"
target_column_name = "your_target"
sheet_name = None
```

## Running the Script

```bash
python XGBoost+SHAP.py
```

## Outputs

The script generates or prints the following outputs:

- Best XGBoost hyperparameters from grid search
- Training and test metrics: R2, RMSE, and MAE
- XGBoost feature-importance plot
- `shap_butterfly_final_custom_color.png`
- A folder named `shap_individual_plots_real_cost` containing per-feature SHAP dependence plots

## Notes

- The script accepts both CSV and Excel input files.
- If the target contains non-positive values, an offset is added before the log transform.
- `openpyxl` is included because pandas may need it when reading `.xlsx` files.
- The script is currently written as a single analysis file exported from a notebook workflow.


