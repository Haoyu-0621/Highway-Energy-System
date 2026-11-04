import pandas as pd
import numpy as np
import traceback
from config import Config

# In-memory cache for Excel data to avoid repeated disk reads
_DATA_CACHE = {
    "load": None,  # Total load table
    "pv_curve": None,  # PV curve table
    "pv_cap": None,  # PV capacity table
    "price_sheets": None,  # Time-of-use electricity price table (all sheets)
}


def resize_to_8760(arr):
    """Pad or truncate array to exactly 8760 hours (one year)."""
    arr = np.nan_to_num(np.array(arr), nan=0.0)
    if len(arr) >= 8760:
        return arr[:8760]
    return np.concatenate([arr, np.zeros(8760 - len(arr))])


# Cached data access functions
def get_cached_pv_capacity():
    """Get cached PV capacity data, loading from disk on first call."""
    if _DATA_CACHE["pv_cap"] is None:
        print("Loading PV capacity table for the first time (cached)...")
        try:
            df = pd.read_excel(Config.path_pv_capacity, engine="openpyxl")
            df.columns = df.columns.astype(str).str.strip()
            _DATA_CACHE["pv_cap"] = df
        except Exception as e:
            print(f"Failed to load PV capacity table: {e}")
            raise e
    return _DATA_CACHE["pv_cap"]


def get_cached_price_sheets():
    """Get cached electricity price sheets, loading from disk on first call."""
    if _DATA_CACHE["price_sheets"] is None:
        print("Loading electricity price sheets for the first time (cached)...")
        try:
            # Read all sheets at once
            dfs = pd.read_excel(Config.path_price, sheet_name=None, engine="openpyxl")
            # Preprocess: strip whitespace from sheet names
            clean_dfs = {k.strip(): v for k, v in dfs.items()}
            _DATA_CACHE["price_sheets"] = clean_dfs
        except Exception as e:
            print(f"Failed to load electricity price sheets: {e}")
            raise e
    return _DATA_CACHE["price_sheets"]


def get_cached_load_data():
    """Get cached total load data, loading from disk on first call."""
    if _DATA_CACHE["load"] is None:
        print("Loading total load data for the first time (cached)...")
        df = pd.read_excel(Config.path_total_load, index_col=0, engine="openpyxl")
        df.columns = df.columns.astype(str).str.strip()
        _DATA_CACHE["load"] = df
    return _DATA_CACHE["load"]


def get_cached_pv_curve():
    """Get cached PV curve data, loading from disk on first call."""
    if _DATA_CACHE["pv_curve"] is None:
        print("Loading PV curve data for the first time (cached)...")
        df = pd.read_excel(Config.path_pv_curve, index_col=0, engine="openpyxl")
        df.columns = df.columns.astype(str).str.strip()
        _DATA_CACHE["pv_curve"] = df
    return _DATA_CACHE["pv_curve"]


def load_pv_info_from_file(target_area):
    """Load PV capacity, roof/shell ratios, and city name for a service area."""
    df = get_cached_pv_capacity()  # Use cached data

    # Find the row corresponding to the target service area
    row = df[df.iloc[:, 0].astype(str).str.strip() == str(target_area).strip()]

    if row.empty:
        raise ValueError(f"Service area not found in PV capacity table: {target_area}")

    def get_val_fuzzy(keywords, default_idx, dtype=float, exclude=None):
        """Search for a value by keyword matching in column names."""
        for col in df.columns:
            if exclude and any(ex_kw in col for ex_kw in exclude):
                continue
            if any(kw in col for kw in keywords):
                try:
                    val = row[col].values[0]
                    if dtype == str:
                        return str(val).strip()
                    else:
                        return float(val)
                except:
                    continue
        try:
            val = row.iloc[0, default_idx]
            if dtype == str:
                return str(val).strip()
            else:
                return float(val)
        except:
            return None

    # Get city name
    city_name = get_val_fuzzy(
        keywords=["所属城市", "City"],
        default_idx=10,
        dtype=str,
    )
    # Get PV capacity
    cap_val = get_val_fuzzy(
        keywords=["System Capacity", "kw", "Kw"],
        default_idx=4,
        dtype=float,
    )
    # Get carport ratio
    ratio_shell = get_val_fuzzy(
        keywords=[
            "光伏车棚比例",
            "Carport Ratio",
        ],
        default_idx=8,
        dtype=float,
    )
    ratio_roof = get_val_fuzzy(
        keywords=[
            "光伏屋顶比例",
            "Roof Ratio",
        ],
        default_idx=9,
        dtype=float,
    )

    if city_name is None or str(city_name).replace(".", "").isnumeric():
        print(f"Service area {target_area} city name read error: '{city_name}'")

    return cap_val, ratio_roof, ratio_shell, city_name


def generate_8760_price_from_city_sheet(city_name):
    """Generate 8760-hour electricity price for a city from its price sheet."""
    if not isinstance(city_name, str) or str(city_name).replace(".", "").isnumeric():
        return None

    try:
        # Use cached sheet dictionary
        sheet_map = get_cached_price_sheets()

        target_sheet = None
        if city_name in sheet_map:
            target_sheet = city_name
        else:
            simple_name = city_name.replace("市", "").replace("地区", "")
            for key in sheet_map.keys():
                if simple_name in key:
                    target_sheet = key
                    break

        if not target_sheet:
            print(f"City not found in price table: {city_name}")
            return None

        df_price = sheet_map[target_sheet]

        if df_price.shape[1] < 25:
            return None

        # Extract 12 months x 24 hours price matrix
        price_matrix = df_price.iloc[0:12, 1:25].values.astype(float)

        # Expand to 8760 hours
        dt_idx = pd.date_range(start="2025-01-01 00:00", periods=8760, freq="h")
        price_8760 = []
        for ts in dt_idx:
            price_8760.append(price_matrix[ts.month - 1, ts.hour])

        return np.array(price_8760)

    except Exception as e:
        print(f"  [Price read error] {city_name}: {e}")
        return None


def load_data_for_area(target_area):
    """Load all data required for optimization for a given service area."""
    try:
        # Load total load (from cache)
        df_load = get_cached_load_data()
        if target_area not in df_load.columns:
            return None, None, None, None, None, None, None
        load_8760 = resize_to_8760(df_load[target_area].values)

        # Load PV curve (from cache)
        df_pv = get_cached_pv_curve()
        pv_vals = np.zeros(8760)
        if target_area in df_pv.columns:
            pv_vals = df_pv[target_area].values
        pv_8760 = resize_to_8760(pv_vals)

        # Load city info
        pv_cap_kW, r_roof, r_shell, city_name = load_pv_info_from_file(target_area)

        # Load electricity price
        price_8760 = generate_8760_price_from_city_sheet(city_name)

        if price_8760 is None:
            return None, None, None, None, None, None, None

        # Convert to dictionary format
        d_pv = {t: pv_8760[t] for t in range(8760)}
        d_load = {t: load_8760[t] for t in range(8760)}
        d_price = {t: price_8760[t] for t in range(8760)}

        return d_pv, d_load, d_price, pv_cap_kW, r_roof, r_shell, city_name

    except Exception as e:
        print(f"Error loading {target_area}: {e}")
        return None, None, None, None, None, None, None


def get_target_areas():
    """Get list of all service area names from the load data."""
    try:
        df = get_cached_load_data()
        return [str(c).strip() for c in df.columns if "Unnamed" not in str(c)]
    except:
        return []


def get_lat_lon(target_area):
    """
    Get longitude and latitude for a service area from the PV capacity table.
    Assumes: Column B = longitude, Column C = latitude (indices 1 and 2).
    """
    try:
        df = get_cached_pv_capacity()
        # Find the row for the target service area
        row = df[df.iloc[:, 0].astype(str).str.strip() == str(target_area).strip()]

        if row.empty:
            return None, None

        # Column B = index 1, Column C = index 2
        lon = row.iloc[0, 1]
        lat = row.iloc[0, 2]

        # Try to convert to float
        try:
            lon = float(lon)
            lat = float(lat)
        except:
            pass

        return lon, lat
    except Exception as e:
        print(f"Failed to get coordinates for {target_area}: {e}")
        return None, None
