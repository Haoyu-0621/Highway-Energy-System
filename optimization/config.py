from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

class Config:
    # DATA PATHS - Modify these to point to your local data files
    # The Excel files should contain the following columns/structure:
    #   - Total load file: service area names as columns, hourly data as rows
    #   - PV curve file: service area names as columns, hourly PV generation
    #   - Price file: multiple sheets named by city, 12 rows x 24 cols (monthly hourly prices)
    #   - PV capacity file: service area info including city, capacity, roof/shell ratios

    path_total_load = REPOSITORY_ROOT / "data" / "processed" / "your_total_load.xlsx"
    path_pv_curve = REPOSITORY_ROOT / "data" / "processed" / "your_pv_curve.xlsx"
    path_price = REPOSITORY_ROOT / "data" / "processed" / "your_price.xlsx"
    path_pv_capacity = REPOSITORY_ROOT / "data" / "processed" / "your_pv_capacity.xlsx"
    result_dir = REPOSITORY_ROOT / "results" / "optimization"

    # Grid carbon emission factor (kgCO2/kWh)
    co2_grid_factor = None # set your co2_grid_factor
    # Feed-in tariff (CNY/kWh)
    price_sell = None #set your price_sell

    # Modify above for your data

    # Battery cost (CNY/kWh)
    cost_bat_capex = 900.0
    # Battery lifetime (years)
    years_bat = 15
    # Battery annual O&M rate (capacity * unit_price * rate)
    rate_om_bat = 0.02

    # PV roof installation cost (CNY/kW)
    cost_pv_roof_capex = 2590.0
    # PV carport installation cost (CNY/kW)
    cost_pv_shell_capex = 4200.0
    # PV lifetime (years)
    years_pv = 20
    # PV annual O&M cost (CNY/kW)
    price_om_pv = 40
    # Discount rate
    rate_discount = 0.05

    # Battery charging efficiency
    eff_ch = 0.95
    # Battery discharging efficiency
    eff_dis = 0.95
    # Minimum SOC
    soc_min = 0.05
    # Maximum SOC
    soc_max = 0.95
    # Battery charging C-rate
    c_rate_ch = 0.2
    # Battery discharging C-rate
    c_rate_dis = 1.0
    # Battery self-discharge rate per hour
    self_discharge_rate = 0.00002
    # Total hours in a year
    hours_total = 8760

    @classmethod
    def validate(cls):
        missing_items = []
        if cls.co2_grid_factor is None:
            missing_items.append("co2_grid_factor")
        if cls.price_sell is None:
            missing_items.append("price_sell")

        if missing_items:
            raise ValueError(
                "Please set the following values in config.py before running: "
                + ", ".join(missing_items)
            )

   