import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import MaxNLocator, AutoMinorLocator, LogLocator, ScalarFormatter, NullLocator, FixedLocator, FuncFormatter
from matplotlib import font_manager
import matplotlib.patheffects as path_effects
from openpyxl.styles import PatternFill, Font
from matplotlib.offsetbox import AnchoredText
from matplotlib.lines import Line2D
from scipy.interpolate import interp1d
from config import Config
from scipy.spatial.distance import cdist

# Font and Plot Style Setup

def setup_fonts():
    """Configure matplotlib for publication-quality figures."""
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.linewidth"] = 1.5

zh_font = font_manager.FontProperties(family="SimSun", size=11)
zh_font_bold = font_manager.FontProperties(family="SimSun", size=12, weight="bold")
zh_font_title = font_manager.FontProperties(family="SimSun", size=15, weight="bold")
setup_fonts()


def make_axis_bold(ax):
    """Make axis lines and ticks bold for emphasis."""
    for spine in ax.spines.values():
        spine.set_linewidth(2.0)
        spine.set_color("black")
    ax.tick_params(which="major", width=2.0, length=6, color="black", labelsize=11)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")


def force_text_bold(text_obj, linewidth=0.6):
    """Apply stroke effect to text for better visibility."""
    if text_obj:
        text_obj.set_path_effects(
            [
                path_effects.withStroke(linewidth=linewidth, foreground="black"),
                path_effects.Normal(),
            ]
        )

# Core Calculation Logic

def calculate_annual_factor(discount_rate, years):
    """Calculate Capital Recovery Factor (CRF)."""
    if discount_rate > 0:
        crf = (discount_rate * (1 + discount_rate) ** years) / (
            (1 + discount_rate) ** years - 1
        )
    else:
        crf = 1 / years
    return crf


def package_result_row(target_area, cap, pv_cap_kW, ratio_roof, ratio_shell, df_hourly):
    """
    Package optimization results into a summary row dictionary.

    Computes:
    - Physical quantities: total load, PV generation, grid exchange
    - Economic costs: PV investment, battery investment, grid costs
    - Carbon emissions
    - Self-sufficiency and self-consumption rates
    """
    # Physical quantities
    total_load = df_hourly["Load"].sum()
    total_pv_gen = df_hourly["PV"].sum()
    total_buy_kwh = df_hourly["P_grid_buy"].sum()
    total_sell_kwh = df_hourly["P_grid_sell"].sum()

    # Economic parameters
    r_pv, n_pv = Config.rate_discount, Config.years_pv
    crf_pv = calculate_annual_factor(r_pv, n_pv)

    r_bat, n_bat = Config.rate_discount, Config.years_bat
    crf_bat = calculate_annual_factor(r_bat, n_bat)

    # PV cost breakdown
    pv_capex_total = (pv_cap_kW * ratio_roof * Config.cost_pv_roof_capex) + (
        pv_cap_kW * ratio_shell * Config.cost_pv_shell_capex
    )
    cost_pv_inv_annual = pv_capex_total * crf_pv
    cost_pv_om_annual = pv_cap_kW * Config.price_om_pv

    # Battery cost breakdown
    bat_capex_total = cap * Config.cost_bat_capex
    cost_bat_inv_annual = bat_capex_total * crf_bat
    cost_bat_om_annual = bat_capex_total * Config.rate_om_bat

    # Grid interaction costs
    cost_grid_buy = (df_hourly["P_grid_buy"] * df_hourly["price_buy"]).sum()
    income_grid_sell = total_sell_kwh * Config.price_sell

    # Total metrics
    total_net_cost = (
        (cost_grid_buy - income_grid_sell)
        + (cost_pv_inv_annual + cost_pv_om_annual)
        + (cost_bat_inv_annual + cost_bat_om_annual)
    )

    total_carbon = total_buy_kwh * Config.co2_grid_factor

    # Rates
    self_sufficiency = 1 - (total_buy_kwh / total_load) if total_load > 0 else 0
    self_consumption = 1 - (total_sell_kwh / total_pv_gen) if total_pv_gen > 0 else 0

    return {
        "Service Area": target_area,
        "Total Load (kWh)": round(total_load, 1),
        "Annual PV Generation (kWh)": round(total_pv_gen, 1),
        "PV Capacity (kW)": round(pv_cap_kW, 1),
        "Carport Ratio": round(ratio_shell, 2),
        "Roof Ratio": round(ratio_roof, 2),
        "Battery Capacity (kWh)": round(cap, 2),
        "Annual PV Investment (CNY)": round(cost_pv_inv_annual, 0),
        "Annual PV O&M (CNY)": round(cost_pv_om_annual, 0),
        "Annual Battery Investment (CNY)": round(cost_bat_inv_annual, 0),
        "Annual Battery O&M (CNY)": round(cost_bat_om_annual, 0),
        "Annual Grid Purchase (kWh)": round(total_buy_kwh, 1),
        "Annual Grid Cost (CNY)": round(cost_grid_buy, 0),
        "Annual Grid Sell (kWh)": round(total_sell_kwh, 1),
        "Annual Grid Income (CNY)": round(income_grid_sell, 0),
        "Annual Net Cost (CNY)": round(total_net_cost, 0),
        "Annual Carbon (kg)": round(total_carbon, 0),
        "Self-Sufficiency Rate (%)": round(self_sufficiency * 100, 2),
        "Self-Consumption Rate (%)": round(self_consumption * 100, 2),
    }


def find_knee_point_index(costs, carbs):
    """
    Find the knee point (compromise solution) on the Pareto curve.

    Uses TOPSIS with Mahalanobis distance:
    - Ideal point: minimum cost and minimum carbon
    - Anti-ideal point: maximum weighted cost and carbon
    - Knee point has maximum closeness to ideal and distance from anti-ideal
    """
    if len(costs) <= 2:
        return 0
    c_arr, e_arr = np.array(costs), np.array(carbs)
    c_min, c_max = c_arr.min(), c_arr.max()
    e_min, e_max = e_arr.min(), e_arr.max()
    c_range = c_max - c_min if c_max != c_min else 1.0
    e_range = e_max - e_min if e_max != e_min else 1.0

    c_norm = (c_arr - c_min) / c_range
    e_norm = (e_arr - e_min) / e_range

    # TOPSIS with Mahalanobis distance
    w_cost, w_emis = 0.5, 0.5
    c_weighted = c_norm * w_cost
    e_weighted = e_norm * w_emis

    # Build data matrix
    X = np.stack([c_weighted, e_weighted], axis=1)

    # Compute inverse covariance matrix
    cov = np.cov(X.T)
    is_pseudo = False
    try:
        VI = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        VI = np.linalg.pinv(cov)
        is_pseudo = True

    # Diagnostics
    print(f"Matrix type: {'Pseudo-Inverse' if is_pseudo else 'Regular Inverse'}")
    print(f"Inverse covariance matrix VI (check off-diagonal elements):")
    print(VI)
    if abs(VI[0][1]) > 1e-5:
        print("Status: Mahalanobis distance active")
    else:
        print("Status: Reduced to Euclidean distance")

    ideal_point = np.array([[0, 0]])
    anti_ideal_point = np.array([[w_cost, w_emis]])

    # Calculate distances
    d_pos = cdist(X, ideal_point, metric="mahalanobis", VI=VI).flatten()
    d_neg = cdist(X, anti_ideal_point, metric="mahalanobis", VI=VI).flatten()

    closeness = d_neg / (d_pos + d_neg + 1e-10)

    best_idx = np.argmax(closeness)
    print(f"Best point index: {best_idx}")
    print(f"Raw data: Cost={costs[best_idx]:.2f}, Carbon={carbs[best_idx]:.2f}")
    print(f"Composite score: {closeness[best_idx]:.4f} (Max)")
    return np.argmax(closeness)

# Export Functions

def save_pareto_details(target_area, pareto_data_list, knee_idx, output_folder):
    """Save Pareto solution details to Excel."""
    rows = []
    n = len(pareto_data_list)
    for i, item in enumerate(pareto_data_list):
        sol_type = ""
        if i == 0:
            sol_type = "Cost-Optimal"
        elif i == n - 1:
            sol_type = "Emission-Optimal"
        elif i == knee_idx:
            sol_type = "Compromise"

        rows.append(
            {
                "Service Area": target_area,
                "Carbon Constraint": item["target"],
                "Annualized Cost (CNY)": item["cost"],
                "Annual Carbon (kg)": item["carb"],
                "Battery Capacity (kWh)": item["cap"],
                "Solution Type": sol_type,
            }
        )
    df = pd.DataFrame(rows)
    path = os.path.join(output_folder, f"{target_area}_pareto_details.xlsx")
    try:
        df.to_excel(path, index=False)
        print(f"  -> [Pareto details] Saved")
    except Exception as e:
        print(f"  -> Save failed: {e}")


def save_hourly_details(target_area, hourly_data_dict, output_folder):
    """Save hourly system operation data to multi-sheet Excel."""
    path = os.path.join(output_folder, f"{target_area}_hourly_system_data.xlsx")
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, df in hourly_data_dict.items():
                if df is not None:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"  -> [Hourly data] Saved")
    except Exception as e:
        print(f"  -> Save failed: {e}")


def save_aggregated_excel(aggregated_data, root_folder, region_name):
    """Save aggregated results across all service areas to Excel."""
    filename = f"{region_name}_results_summary.xlsx"
    save_path = os.path.join(root_folder, filename)
    try:
        with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
            header_font = Font(bold=True)
            sheet_map = {
                "min_cost": "Cost_Optimal",
                "min_carb": "Carbon_Optimal",
                "knee_point": "Compromise",
            }

            for key, sheet_name in sheet_map.items():
                data_list = aggregated_data.get(key, [])
                if not data_list:
                    continue

                df = pd.DataFrame(data_list)
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                ws = writer.sheets[sheet_name]
                for cell in ws[1]:
                    cell.font = header_font

                # Auto-adjust column widths
                for column in ws.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    try:
                        for cell in column:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        adjusted_width = (max_length + 2) * 1.1
                        ws.column_dimensions[column[0].column_letter].width = (
                            adjusted_width
                        )
                    except:
                        pass
        print(f"\n[Success] Summary file generated: {save_path}")
    except Exception as e:
        print(f"[Error] Summary save failed: {e}")


# Pareto Curve Plotting

def plot_pareto_curve(
    target_area, pareto_results, knee_idx, output_folder, no_bat_data=None, lon=None, lat=None
):
    """Plot Pareto curve with cost on x-axis, carbon on y-axis, and battery capacity on secondary axis."""
    if not pareto_results:
        return

    # Data preparation
    costs = np.array([r["cost"] for r in pareto_results]) / 10000.0  # 10k CNY
    carbs = np.array([r["carb"] for r in pareto_results]) / 1000.0   # tons
    caps = np.array([r["cap"] for r in pareto_results])             # kWh

    # Sort by capacity
    sort_idx = np.argsort(caps)
    caps_sorted = caps[sort_idx]
    costs_sorted = costs[sort_idx]

    unique_caps, unique_indices = np.unique(caps_sorted, return_index=True)
    unique_costs = costs_sorted[unique_indices]

    fig1, ax1 = plt.subplots(figsize=(9, 6))

    title_obj = ax1.set_title(target_area, fontproperties=zh_font_title, pad=0, y=1.05)
    force_text_bold(title_obj)

    # Add coordinates if available
    if lon is not None and lat is not None:
        try:
            coord_str = f"$\mathrm{{({float(lon):.2f}^\circ N, {float(lat):.2f}^\circ E)}}$"
            ax1.text(0.5, 1.01, coord_str,
                     transform=ax1.transAxes, ha='center', va='bottom', fontsize=12)
        except:
            pass

    ax1.plot(carbs, costs, color="black", linestyle="-", linewidth=2.0, marker="o", markersize=4, zorder=1)
    ax1.scatter(carbs[0], costs[0], color="blue", s=50, zorder=5, label="Cost-Optimal", edgecolors="black")
    ax1.scatter(carbs[-1], costs[-1], color="green", s=50, zorder=5, label="Carbon-Optimal", edgecolors="black")
    ax1.scatter(carbs[knee_idx], costs[knee_idx], color="red", s=50, marker="o", zorder=6, label="Compromise", edgecolors="black")

    # Margin settings
    x_margin = (max(carbs) - min(carbs)) * 0.05 if len(carbs) > 1 else 0.1
    y_margin = (max(costs) - min(costs)) * 0.05 if len(costs) > 1 else 0.1
    ax1.set_xlim(min(carbs) - x_margin, max(carbs) + x_margin)
    ax1.set_ylim(min(costs) - y_margin, max(costs) + y_margin)

    make_axis_bold(ax1)
    xlabel1 = ax1.set_xlabel("Carbon Emissions (tons)", fontproperties=zh_font_bold)
    ylabel1 = ax1.set_ylabel("Total Cost (10k CNY)", fontproperties=zh_font_bold)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    ax2.set_ylim(ax1.get_ylim())

    # Helper functions for nice axis ticks
    def get_inward_rounded_endpoints(v_min, v_max):
        """Get nicely rounded axis endpoints that are inside the data range."""
        if v_max <= v_min: return v_min, v_max

        start_order = 10 ** int(np.floor(np.log10(v_min))) if v_min > 0 else 1
        nice_start = np.ceil(v_min / start_order) * start_order
        if nice_start >= v_max: nice_start = v_min

        end_order = 10 ** int(np.floor(np.log10(v_max)) - 1) if v_max > 10 else 1
        nice_end = np.floor(v_max / end_order) * end_order
        if nice_end <= nice_start: return v_min, v_max

        return nice_start, nice_end

    def generate_natural_ticks(start, end):
        """Generate natural-looking tick positions with ~5-6 ticks."""
        if start >= end: return np.array([start])

        # Calculate ideal step size
        span = end - start
        raw_step = span / 5.0

        # Find nearest "1, 2, 2.5, 5" * 10^n step
        power = 10 ** np.floor(np.log10(raw_step))
        fraction = raw_step / power

        if fraction < 1.5: nice_step = 1 * power
        elif fraction < 2.5: nice_step = 2 * power
        elif fraction < 3.5: nice_step = 2.5 * power
        elif fraction < 7.5: nice_step = 5 * power
        else: nice_step = 10 * power

        # Generate aligned grid points
        first_grid = np.ceil(start / nice_step) * nice_step
        last_grid = np.floor(end / nice_step) * nice_step

        if first_grid > last_grid:
            inner_ticks = np.array([])
        else:
            inner_ticks = np.arange(first_grid, last_grid + nice_step*0.01, nice_step)

        final_ticks = [start]

        # Add middle ticks that are sufficiently away from endpoints
        for t in inner_ticks:
            if abs(t - start) > 0.25 * nice_step:
                final_ticks.append(t)
        if len(final_ticks) > 0 and abs(end - final_ticks[-1]) < 0.25 * nice_step:
            final_ticks[-1] = end
        else:
            final_ticks.append(end)

        return np.array(final_ticks)

    # Generate ticks
    min_cap_val = np.min(caps)
    max_cap_val = np.max(caps)

    tick_start, tick_end = get_inward_rounded_endpoints(min_cap_val, max_cap_val)
    target_cap_ticks = generate_natural_ticks(tick_start, tick_end)

    # Map capacity to cost for secondary axis
    tick_locs = []
    tick_labels = []

    if len(unique_caps) > 1 and len(target_cap_ticks) > 0:
        f_interp = interp1d(unique_caps, unique_costs, kind='linear', fill_value="extrapolate")
        y_min_view, y_max_view = ax1.get_ylim()

        for cap_val in target_cap_ticks:
            loc_cost = f_interp(cap_val)

            # View safety check
            margin = (y_max_view - y_min_view) * 0.1
            if (y_min_view - margin) <= loc_cost <= (y_max_view + margin):
                tick_locs.append(loc_cost)

                # Format label
                if abs(cap_val - round(cap_val)) < 0.1:
                    lbl = f"{int(cap_val)}"
                else:
                    lbl = f"{cap_val:.1f}"
                tick_labels.append(lbl)

                # Add dashed helper line
                ax1.hlines(y=loc_cost, xmin=ax1.get_xlim()[0], xmax=ax1.get_xlim()[1],
                           colors="gray", linestyles=":", alpha=0.3, linewidth=0.8)

    ax2.set_yticks(tick_locs)
    ax2.set_yticklabels(tick_labels, fontweight="bold", fontsize=10, family="serif")

    make_axis_bold(ax2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_linewidth(2.0)

    ylabel2 = ax2.set_ylabel("Battery Capacity (kWh)", fontproperties=zh_font_bold, rotation=270, labelpad=20)
    force_text_bold(ylabel1)
    force_text_bold(xlabel1)
    force_text_bold(ylabel2)

    legend = ax1.legend(
        prop={"family": "SimSun", "size": 9, "weight": "bold"},
        loc="upper right", frameon=True,
    )
    legend.get_frame().set_alpha(0.9)
    legend.get_frame().set_linewidth(0.0)

    # Add no-battery baseline info
    if no_bat_data:
        info_text = (
            f"No Battery Baseline:\n"
            f"Cost: {no_bat_data['cost']/10000:.1f} 10k CNY\n"
            f"Carbon: {no_bat_data['carb']/1000:.1f} t"
        )
        ax1.text(
            0.98, 0.84, info_text,
            transform=ax1.transAxes,
            ha="right", va="top", multialignment="left",
            fontproperties=zh_font_bold,
            fontsize=9,
            bbox=dict(facecolor='none', edgecolor='none', alpha=0.0)
        )

    plt.tight_layout()
    img_name = f"{target_area}_pareto_curve.png"
    save_path = os.path.join(output_folder, img_name)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig1)
    print(f"  -> [Figure] Saved")


def plot_combined_pareto(province_name, all_pareto_data, output_folder):
    """Plot combined Pareto fronts for all service areas, colored by city."""
    if not all_pareto_data:
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    title_obj = ax.set_title(
        f"{province_name} - Combined Pareto Front", fontproperties=zh_font_title, pad=15
    )
    force_text_bold(title_obj)

    # Color map by city
    unique_cities = sorted(list(set(d["city"] for d in all_pareto_data)))
    cmap = plt.get_cmap("tab20")
    colors = [cmap(i) for i in np.linspace(0, 1, len(unique_cities))]
    city_color_map = dict(zip(unique_cities, colors))

    for entry in all_pareto_data:
        city = entry["city"]
        area = entry["area"]
        results = entry["results"]
        knee_idx = entry["knee_idx"]

        color = city_color_map.get(city, "black")
        costs = np.array([r["cost"] for r in results]) / 10000.0  # 10k CNY
        carbs = np.array([r["carb"] for r in results]) / 1000.0  # tons

        ax.plot(carbs, costs, color=color, linestyle="-", linewidth=2.0, alpha=0.7)

    # Legend
    legend_elements = []
    for city in unique_cities:
        legend_elements.append(
            Line2D([0], [0], color=city_color_map[city], lw=2, label=city)
        )

    legend = ax.legend(
        handles=legend_elements,
        prop={"family": "SimSun", "size": 10, "weight": "bold"},
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        frameon=True,
        title="City",
    )
    legend.get_title().set_fontproperties(zh_font_bold)
    frame = legend.get_frame()
    frame.set_alpha(0.9)
    frame.set_linewidth(0.0)

    make_axis_bold(ax)
    xlabel = ax.set_xlabel("Carbon Emissions (tons)", fontproperties=zh_font_bold)
    ylabel = ax.set_ylabel("Total Cost (10k CNY)", fontproperties=zh_font_bold)
    force_text_bold(xlabel)
    force_text_bold(ylabel)

    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    save_path = os.path.join(output_folder, f"{province_name}_combined_pareto.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[Summary figure] Saved to: {save_path}")
