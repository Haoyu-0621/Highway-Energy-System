# Supporting data

## Dataset scope

- `data1/service_area_data.csv` provides **3,094 annual service-area summary records**, with one row per service area and 11 columns.
- The 8760-hour profiles in `data2/` cover **seven selected typical service areas, one per major region of China**. Each typical site has **8,760 observations at 1-hour resolution** for a 365-day year.
- `data2/` also contains tunnel information and separate 24-hour load tables. See also [the original description](data2/readme.txt).

## data1 — annual summary for 3,094 service areas

File `data1/service_area_data.csv` is a comma-separated UTF-8 table with a header row. Annual electricity fields use kWh/year, installation area uses m², and installed capacity uses kW.

| Exact column name | Meaning | Unit |
|---|---|---|
| `Service Area Name` | Service-area name | Text |
| `Longitude (deg E)` | Longitude | Degrees east |
| `Latitude (deg N)` | Latitude | Degrees north |
| `PV Installation Area (m2)` | PV installation area | m² |
| `PV Installed Capacity (kW)` | PV installed capacity | kW |
| `Annual PV Generation (kWh/year)` | Annual PV electricity generation | kWh/year |
| `Annual Building Electricity Consumption (kWh/year)` | Annual building electricity consumption | kWh/year |
| `Annual EV Charging Electricity Consumption (kWh/year)` | Annual EV charging electricity consumption | kWh/year |
| `Annual Tunnel Electricity Consumption (kWh/year)` | Annual tunnel electricity consumption | kWh/year |
| `Province` | Province-level region | Text |
| `Region` | Major geographical region | Text |

`Region` contains East China, North China, Northeast China, Central China, South China, Southwest China, and Northwest China. The tunnel field records tunnel electricity consumption.

## data2 — seven regional typical sites and supporting tables

The selected typical sites are listed in `data2/2/area.xlsx`. The PV, building, and EV charging hourly workbooks use the same site names and regional labels.

| Region in data1 | Region label in data2 | Selected typical service area |
|---|---|---|
| North China (华北) | `North` | `shangdian_Service_Area` |
| Northeast China (东北) | `Northeast` | `dongmei_Service_Area` |
| Northwest China (西北) | `Northwest` | `linxia_Service_Area` |
| Central China (华中) | `Central` | `sanli_Service_Area` |
| Southwest China (西南) | `Southwest` | `anxian_Service_Area` |
| East China (华东) | `Southeast` | `beian_Service_Area` |
| South China (华南) | `South` | `bajia_Service_Area` |

The original workbooks use `Southeast` for the eastern typical site. Use the mapping above when relating this label to `East China` in the annual summary.

| File | Contents and time coverage |
|---|---|
| `data2/1/tunnel.xlsx` | Tunnel attributes, including name, length, road, route number, and district ID |
| `data2/2/area.xlsx` | Seven typical sites, coordinates, site attributes, and PV-installable areas |
| `data2/3/pv.xlsx` | PVsyst simulated generation, 8,760 hourly rows for each of the seven typical sites |
| `data2/4/building.xlsx` | Building load profiles, 8,760 hourly rows for each of the seven typical sites |
| `data2/5/charge.xlsx` | EV charging load profiles, 8,760 hourly rows for each of the seven typical sites |
| `data2/6/service_area_24h_load.xlsx` | Service-area daily load profiles with hour columns `1`–`24` |
| `data2/6/tunnel_24h_load.xlsx` | Tunnel daily load profiles with hour columns `1`–`24` |

### Hourly workbook layout and reading requirements

The three 8760-hour workbooks each have two header rows followed by 8,760 data rows. Row 1 holds region labels, row 2 holds `Time` and the seven selected service-area names, and column A contains time labels. The seven site series occupy columns B–H. `building.xlsx` also contains empty trailing columns, so select columns A–H when loading these profiles.

The source time labels omit a year and time zone. Their first label is `01/01 01:00:00` and their final label is `12/31 00:00:00`. Preserve the supplied row order and confirm the time-label convention when constructing a datetime index. The hourly value columns have no explicit unit labels in their headers, so confirm the source scaling when preparing model inputs.

Python 3.11 with the root `requirements.txt` provides pandas and openpyxl for reading these files. After installing it, run this example from the repository root.

```python
import pandas as pd

annual = pd.read_csv("data/data1/service_area_data.csv", encoding="utf-8-sig")
pv_hourly = pd.read_excel("data/data2/3/pv.xlsx", header=1, usecols="A:H")
building_hourly = pd.read_excel("data/data2/4/building.xlsx", header=1, usecols="A:H")
ev_hourly = pd.read_excel("data/data2/5/charge.xlsx", header=1, usecols="A:H")

assert len(annual) == 3094
assert all(len(table) == 8760 for table in (pv_hourly, building_hourly, ev_hourly))
```

## Model-ready inputs

The optimization loader expects four configured workbooks:

- Total hourly load: first column is an index; remaining columns are service-area names.
- Hourly PV generation: first column is an index; service-area columns must match the load table.
- Electricity prices: one worksheet per city, a header row, then 12 month rows; first column is the month and the next 24 columns are hourly prices.
- PV capacity: first column is the service-area name; include `City`, `System Capacity`, `Carport Ratio`, and `Roof Ratio` columns. Longitude and latitude, when used, occupy the second and third columns. Ratios are fractional values.

XGBoost requires a numeric target column and predictor columns in a CSV or Excel table. Set the target explicitly in the script. The complete training table, preprocessing mapping, and four model-ready workbooks are not separately identified in this supporting dataset.

Prepare compatible inputs and update the configuration; do not rename an arbitrary supporting workbook to a placeholder name and assume it matches the required schema. The suggested `processed/` directory is a convention for future model-ready inputs, not a claim that these files are already supplied.
