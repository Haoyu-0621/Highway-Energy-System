# Highway Energy System Optimization

Multi-objective planning of photovoltaic (PV) and battery energy storage systems (BESS) for highway service areas, balancing annual cost and carbon emissions.

## Features

- Pareto-front generation using the epsilon-constraint method.
- Compromise-solution selection using TOPSIS with Mahalanobis distance.
- Cost-optimal, carbon-optimal, and compromise-solution analysis.
- Annual operation modeling at 1-hour resolution using Pyomo and Gurobi.

## Project Structure

```text
optimization/
├── main.py                # Main entry point
├── config.py              # Model parameters
├── data_loader.py         # Data loading
├── optimization_model.py  # Optimization model
├── solver_engine.py       # Solver and scenario analysis
├── visualization.py       # Plotting and result export
├── requirements.txt       # Python dependencies
└── README.md
```

## Requirements

Python 3.11 and a valid Gurobi license are required. Dependencies include Pyomo, gurobipy, pandas, NumPy, Matplotlib, openpyxl, and SciPy. Library versions are listed in [requirements.txt](requirements.txt).

From the repository root, install the module dependencies in its Python environment.

```bash
python -m pip install -r optimization/requirements.txt
```

## Data Requirements

- **Hourly electricity demand** — building, EV charging, and applicable tunnel loads, combined for each service area. The seven typical-site building and EV charging profiles are provided in [building.xlsx](../data/data2/4/building.xlsx) and [charge.xlsx](../data/data2/5/charge.xlsx). Supporting 24-hour service-area and tunnel load profiles are in [data2/6](../data/data2/6).
- **Hourly PV generation** — a full-year generation curve consistent with the site's installed PV capacity. [pv.xlsx](../data/data2/3/pv.xlsx) provides PVsyst simulation profiles for the seven typical sites.
- **PV site parameters** — installed capacity and roof/carport capacity shares for installation-cost calculations. [area.xlsx](../data/data2/2/area.xlsx) supplies the seven typical sites' coordinates and effective roof, carport, and total PV installation areas. Derive capacity shares from the roof and carport system design, using their area shares when installed capacity per unit area is the same. Supplement the site attributes with installed capacity consistent with the PV simulation and the city used to select tariffs, then map them to the loader's PV parameter input.
- **Electricity tariffs** — local time-of-use purchase tariffs for each site's city, supplied for the study period.

The typical-site PV, building, and EV charging profiles each contain **8,760 observations at 1-hour resolution**, covering one selected service area from each of China's seven major regions. The annual summary for **3,094 service areas**, including installed PV capacity and annual generation and consumption, is provided in [data1](../data/data1/service_area_data.csv). See the [data description](../data/README.md) for the site mapping and field definitions.

## Configuration

In `config.py`, set the grid carbon emission factor `co2_grid_factor` (kgCO₂/kWh) and electricity sale price `price_sell` (CNY/kWh) for the study region.
