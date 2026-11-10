# Supporting data

## Dataset scope

- `data1/service_area_data.csv` provides **3,094 annual service-area summary records**, with one row per service area and 11 columns.
- `data1/tunnel_data.csv` provides **6,243 tunnel records**, including tunnel length, province, associated facility, and distance to that facility.
- The 8760-hour profiles in `data2/` cover **seven selected typical service areas, one per major region of China**. Each typical site has **8,760 observations at 1-hour resolution** for a 365-day year.
- `data2/` also contains tunnel information and separate 24-hour load tables. See also [the original description](data2/readme.txt).

## data1 — service-area summaries and tunnel attributes

### Annual service-area data

File `data1/service_area_data.csv` is a comma-separated UTF-8 table with a header row. Annual electricity fields use kWh/year, installation area uses m², and installed capacity uses kW.

<table width="100%">
  <thead>
    <tr>
      <th width="52%" align="left">Exact column name</th>
      <th width="36%" align="left">Meaning</th>
      <th width="12%" align="left">Unit</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="left"><code>Service Area Name</code></td>
      <td align="left">Service-area name</td>
      <td align="left">Text</td>
    </tr>
    <tr>
      <td align="left"><code>Longitude (deg E)</code></td>
      <td align="left">Longitude</td>
      <td align="left">Degrees east</td>
    </tr>
    <tr>
      <td align="left"><code>Latitude (deg N)</code></td>
      <td align="left">Latitude</td>
      <td align="left">Degrees north</td>
    </tr>
    <tr>
      <td align="left"><code>PV Installation Area (m2)</code></td>
      <td align="left">PV installation area</td>
      <td align="left">m²</td>
    </tr>
    <tr>
      <td align="left"><code>PV Installed Capacity (kW)</code></td>
      <td align="left">PV installed capacity</td>
      <td align="left">kW</td>
    </tr>
    <tr>
      <td align="left"><code>Annual PV Generation (kWh/year)</code></td>
      <td align="left">Annual PV electricity generation</td>
      <td align="left">kWh/year</td>
    </tr>
    <tr>
      <td align="left"><code>Annual Building Electricity Consumption (kWh/year)</code></td>
      <td align="left">Annual building electricity consumption</td>
      <td align="left">kWh/year</td>
    </tr>
    <tr>
      <td align="left"><code>Annual EV Charging Electricity Consumption (kWh/year)</code></td>
      <td align="left">Annual EV charging electricity consumption</td>
      <td align="left">kWh/year</td>
    </tr>
    <tr>
      <td align="left"><code>Annual Tunnel Electricity Consumption (kWh/year)</code></td>
      <td align="left">Annual tunnel electricity consumption</td>
      <td align="left">kWh/year</td>
    </tr>
    <tr>
      <td align="left"><code>Province</code></td>
      <td align="left">Province-level region</td>
      <td align="left">Text</td>
    </tr>
    <tr>
      <td align="left"><code>Region</code></td>
      <td align="left">Major geographical region</td>
      <td align="left">Text</td>
    </tr>
  </tbody>
</table>

`Region` contains East China, North China, Northeast China, Central China, South China, Southwest China, and Northwest China. The tunnel field records tunnel electricity consumption.

### Tunnel data

`data1/tunnel_data.csv` contains five fields — `Tunnel Name`, `Tunnel Length (m)`, `Province`, `Associated Facility Name`, and `Distance to Facility (m)`. Length and distance are in metres. Associated facilities include service areas, parking areas, and other roadside rest facilities. Place names use romanized Chinese with English facility types, and provinces use English names.

## data2 — seven regional typical sites and supporting tables

The selected typical sites are listed in `data2/2/area.xlsx`. The PV, building, and EV charging hourly workbooks use the same site names and regional labels.

<table width="100%">
  <thead>
    <tr>
      <th width="32%" align="left">Region in data1</th>
      <th width="28%" align="left">Region label in data2</th>
      <th width="40%" align="left">Selected typical service area</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="left">North China (华北)</td>
      <td align="left"><code>North</code></td>
      <td align="left"><code>shangdian_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">Northeast China (东北)</td>
      <td align="left"><code>Northeast</code></td>
      <td align="left"><code>dongmei_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">Northwest China (西北)</td>
      <td align="left"><code>Northwest</code></td>
      <td align="left"><code>linxia_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">Central China (华中)</td>
      <td align="left"><code>Central</code></td>
      <td align="left"><code>sanli_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">Southwest China (西南)</td>
      <td align="left"><code>Southwest</code></td>
      <td align="left"><code>anxian_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">East China (华东)</td>
      <td align="left"><code>Southeast</code></td>
      <td align="left"><code>beian_Service_Area</code></td>
    </tr>
    <tr>
      <td align="left">South China (华南)</td>
      <td align="left"><code>South</code></td>
      <td align="left"><code>bajia_Service_Area</code></td>
    </tr>
  </tbody>
</table>

The original workbooks use `Southeast` for the eastern typical site. Use the mapping above when relating this label to `East China` in the annual summary.

<table width="100%">
  <thead>
    <tr>
      <th width="38%" align="left">File</th>
      <th width="62%" align="left">Contents and time coverage</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="left"><code>data2/1/tunnel.xlsx</code></td>
      <td align="left">Tunnel attributes, including name, length, road, route number, and district ID</td>
    </tr>
    <tr>
      <td align="left"><code>data2/2/area.xlsx</code></td>
      <td align="left">Seven typical sites, coordinates, site attributes, and PV-installable areas</td>
    </tr>
    <tr>
      <td align="left"><code>data2/3/pv.xlsx</code></td>
      <td align="left">PVsyst simulated generation, 8,760 hourly rows for each of the seven typical sites</td>
    </tr>
    <tr>
      <td align="left"><code>data2/4/building.xlsx</code></td>
      <td align="left">Building load profiles, 8,760 hourly rows for each of the seven typical sites</td>
    </tr>
    <tr>
      <td align="left"><code>data2/5/charge.xlsx</code></td>
      <td align="left">EV charging load profiles, 8,760 hourly rows for each of the seven typical sites</td>
    </tr>
    <tr>
      <td align="left"><code>data2/6/service_area_24h_load.xlsx</code></td>
      <td align="left">Service-area daily load profiles with hour columns <code>1</code>–<code>24</code></td>
    </tr>
    <tr>
      <td align="left"><code>data2/6/tunnel_24h_load.xlsx</code></td>
      <td align="left">Tunnel daily load profiles with hour columns <code>1</code>–<code>24</code></td>
    </tr>
  </tbody>
</table>

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

## Using the data with the models

For optimization, combine the supplied profiles and site attributes with the study's PV system parameters and local electricity tariffs. See the [optimization data requirements](../optimization/README.md#data-requirements).

For XGBoost and SHAP analysis, select the predictor variables and numeric target for the research question as described in the [analysis data requirements](../xgboost-shap/README.md#data-requirements).
