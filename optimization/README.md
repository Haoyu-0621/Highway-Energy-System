> Consolidated repository: see the [main README](../README.md) and [shared data notes](../data/README.md). This module has its own Python environment. Input paths are resolved relative to the repository through `REPOSITORY_ROOT`; edit the placeholders before running.

## Overview

This code implements a multi-objective optimization framework for planning distributed photovoltaic (PV) and battery energy storage systems (BESS). The framework generates Pareto fronts trading off **annual cost** vs. **carbon emissions**, enabling decision-makers to explore the compromise between economic and environmental objectives.

### Key Features

- **Pareto Front Generation**: Uses epsilon-constraint method to systematically explore cost-carbon trade-offs
- **Knee Point Detection**: Employs TOPSIS with Mahalanobis distance to identify the optimal compromise solution
- **Multi-Scenario Analysis**: Computes cost-optimal, carbon-optimal, and compromise scenarios
- **Hourly Simulation**: Full 8760-hour annual simulation using Pyomo + Gurobi

## Requirements

- Python 3.11
- [Pyomo](http://www.pyomo.org/) - Optimization modeling
- [Gurobi Optimizer](https://www.gurobi.com/) - MILP solver (license required)
- pandas, numpy - Data processing
- matplotlib - Visualization
- openpyxl - Excel file I/O
- scipy - Scientific computing

**Python & Library Versions** (see `requirements.txt`):
- Python 3.11
- pyomo == 6.9.5
- pandas == 2.3.3
- numpy == 1.26.4
- matplotlib == 3.10.7
- openpyxl == 3.1.5
- scipy == 1.16.3
- gurobipy == 12.0.3

Install dependencies:
```bash
pip install -r requirements.txt
```

Note: Gurobi must be installed separately with a valid license.

## Data Requirements

The code expects four Excel data files. **You must prepare your own data files** matching the structure described below. Configure the file paths in `config.py`.

### 1. Total Load File (`path_total_load`)

| Column | Description |
|--------|-------------|
| (index) | Date/time index (0-8759 hours) |
| Service Area 1 | Hourly load in kWh |
| Service Area 2 | Hourly load in kWh |
| ... | ... |

### 2. PV Curve File (`path_pv_curve`)

| Column | Description |
|--------|-------------|
| (index) | Date/time index (0-8759 hours) |
| Service Area 1 | Hourly PV generation in kWh |
| Service Area 2 | Hourly PV generation in kWh |
| ... | ... |

### 3. Electricity Price File (`path_price`)

Contains multiple sheets, one per city. Each sheet:

| | 1 | 2 | ... | 24 |
|---|---|---|---|---|
| **Jan** | price | price | ... | price |
| **Feb** | price | price | ... | price |
| ... | ... | ... | ... | ... |
| **Dec** | price | price | ... | price |

Prices in CNY/kWh.

### 4. PV Capacity File (`path_pv_capacity`)

| Column | Description |
|--------|-------------|
| A | Service Area Name |
| B | Longitude |
| C | Latitude |
| D | System Capacity (kW) |
| ... | (Other columns for roof/carport ratios) |

## Configuration

Edit `config.py` to set your data paths and parameters:

```python
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

class Config:
    # Paths to your data files
    path_total_load = REPOSITORY_ROOT / "data" / "processed" / "your_total_load.xlsx"
    path_pv_curve = REPOSITORY_ROOT / "data" / "processed" / "your_pv_curve.xlsx"
    path_price = REPOSITORY_ROOT / "data" / "processed" / "your_price.xlsx"
    path_pv_capacity = REPOSITORY_ROOT / "data" / "processed" / "your_pv_capacity.xlsx"
    result_dir = REPOSITORY_ROOT / "results" / "optimization"

    # Grid parameters
    co2_grid_factor = None  # Replace with your grid emission factor (kgCO2/kWh)
    price_sell = None  # Replace with your feed-in tariff (CNY/kWh)

    # Battery parameters
    cost_bat_capex = 900.0  # CNY/kWh
    years_bat = 15
    eff_ch = 0.95
    eff_dis = 0.95
```

`co2_grid_factor` and `price_sell` are intentionally left as `None` because they depend on the user's local project assumptions. You must fill them in before running the code.

## Usage

1. Prepare your data files and update the paths in `config.py`

2. Fill in `co2_grid_factor` and `price_sell` in `config.py`

3. Run the main optimization:
```bash
python main.py
```

The code will:
- Automatically detect all service areas from your data
- Run cost-optimal, carbon-optimal, and Pareto scans for each area
- Save results to `../results/optimization/{Region}/` (repository-relative configuration)

### Output Files

For each service area:
- `{area}_pareto_details.xlsx` - All Pareto solution points
- `{area}_hourly_system_data.xlsx` - Hourly operation data (cost-optimal, carbon-optimal, compromise)
- `{area}_pareto_curve.png` - Pareto front visualization

Aggregated:
- `{region}_results_summary.xlsx` - Summary of all areas

## Project Structure

```
.
├── main.py                # Main entry point
├── config.py              # Configuration and parameters
├── data_loader.py         # Data loading and caching
├── optimization_model.py  # Pyomo optimization model
├── solver_engine.py       # Solver interface and scenarios
├── visualization.py       # Plotting and export functions
├── README.md              # This file
├── requirements.txt       # Pinned Python dependencies
└── ../results/optimization/  # Output directory at repository level
```

## Notes

- **Gurobi License**: You need a valid Gurobi license to run the optimization. Academic licenses are free.
- **Column Names**: The data loader searches for specific keywords in column names (e.g., "所属城市" for city, "System Capacity" for capacity). Update `data_loader.py` if your column names differ.
- **Missing Data**: The code handles missing service areas gracefully by skipping them.
- **Pinned Dependencies**: `requirements.txt` uses exact versions to improve reproducibility when others clone the repository.
