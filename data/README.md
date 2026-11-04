# Supporting data

The original dataset is preserved in `data2/`. See also [the original description](data2/readme.txt).

| File | Description from the supplied dataset notes |
|---|---|
| `data2/1/tunnel.xlsx` | Tunnel geographical locations |
| `data2/2/area.xlsx` | Service-area geographical locations and PV-installable areas |
| `data2/3/pv.xlsx` | PVsyst simulated generation data |
| `data2/4/building.xlsx` | Building load profiles |
| `data2/5/charge.xlsx` | EV charging load profiles |
| `data2/6/service_area_24h_load.xlsx` | Service-area 24-hour load data |
| `data2/6/tunnel_24h_load.xlsx` | Tunnel 24-hour load data |

These descriptions reflect the supplied notes and file names; workbook schemas have not been validated against either model in this integration.

## Model-ready inputs

The optimization loader expects four configured workbooks:

- Total hourly load: first column is an index; remaining columns are service-area names.
- Hourly PV generation: first column is an index; service-area columns must match the load table.
- Electricity prices: one worksheet per city, a header row, then 12 month rows; first column is the month and the next 24 columns are hourly prices.
- PV capacity: first column is the service-area name; include `City`, `System Capacity`, `Carport Ratio`, and `Roof Ratio` columns. Longitude and latitude, when used, occupy the second and third columns. Ratios are fractional values.

XGBoost requires a numeric target column and predictor columns in a CSV or Excel table. Set the target explicitly in the script. The complete training table, preprocessing mapping, and four model-ready workbooks are not separately identified in this supporting dataset.

Prepare compatible inputs and update the configuration; do not rename an arbitrary supporting workbook to a placeholder name and assume it matches the required schema. The suggested `processed/` directory is a convention for future model-ready inputs, not a claim that these files are already supplied.
