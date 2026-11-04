import numpy as np
import pandas as pd
import os
from pyomo.environ import *
from config import Config
from optimization_model import create_model
from concurrent.futures import ProcessPoolExecutor, as_completed


# Data Extraction Helpers

def extract_hourly_data(model, d_pv, d_load, d_price):
    """Extract hourly operation data from solved model into a DataFrame."""
    data = []
    for t in model.T:
        row = {
            "时间": t + 1,
            "P_grid_buy": value(model.P_grid_buy[t]),
            "P_grid_sell": value(model.P_grid_sell[t]),
            "P_ch": value(model.P_ch[t]),
            "P_disch": value(model.P_dis[t]),
            "SOC": value(model.SOC[t]),
            "PV": d_pv[t],
            "Load": d_load[t],
            "price_buy": d_price[t],
        }
        data.append(row)
    return pd.DataFrame(data)


# Cost Calculation Helpers

def calc_pv_annual_cost(pv_cap_kW, ratio_roof, ratio_shell):
    """Calculate annualized PV cost (investment + O&M)."""
    r, n = Config.rate_discount, Config.years_pv
    crf_pv = (r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else 1 / n
    capex_total = (pv_cap_kW * ratio_roof * Config.cost_pv_roof_capex) + (
        pv_cap_kW * ratio_shell * Config.cost_pv_shell_capex
    )
    return (capex_total * crf_pv) + (pv_cap_kW * Config.price_om_pv)


def get_bat_factor():
    """Calculate annualized battery cost factor (investment + O&M per kWh)."""
    r, n = Config.rate_discount, Config.years_bat
    crf_bat = (r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else 1 / n
    return Config.cost_bat_capex * (crf_bat + Config.rate_om_bat)


def filter_pareto_efficient_with_target(results):
    """
    Filter results to keep only Pareto-efficient points.
    Sort by cost and keep points with significantly lower carbon emissions.
    """
    # Sort by cost
    results.sort(key=lambda x: x["cost"])
    clean_results = []
    min_carb_so_far = float("inf")
    for res in results:
        carb = res["carb"]
        # Only keep if carbon is significantly lower than current minimum
        if carb < min_carb_so_far - 1e-4:
            clean_results.append(res)
            min_carb_so_far = carb
    return clean_results


# No PV No Battery Baseline Scenario (Grid-Only)

def run_no_battery_scenario(d_load, d_price):
    """
    Run simulation without PV and battery (grid-only baseline).
    Returns cost and carbon for pure grid trading scenario.
    """
    total_buy_cost = 0.0
    total_carbon = 0.0

    # Simulate hourly operation (grid only, no PV, no battery)
    for t in range(Config.hours_total):
        load = d_load.get(t, 0)
        price = d_price.get(t, 0)

        total_buy_cost += load * price
        total_carbon += load * Config.co2_grid_factor

    total_net_cost = total_buy_cost
    print(f"Grid-only baseline: Cost={total_net_cost:,.0f}, Carbon={total_carbon:,.0f}")

    return {
        "cap": 0.0,
        "cost": total_net_cost,
        "carb": total_carbon,
        "target": "No Battery",
        "ok": True,
    }


# Epsilon-Constraint Single Point Solver (for parallel execution)

def _solve_single_epsilon(args):
    """
    Solve a single epsilon-constraint point.
    Minimizes cost with a carbon emission upper bound (target).
    """
    target, d_pv, d_load, d_price, pv_cap_kW, bat_factor, cost_pv, delta = args
    model = create_model(d_pv, d_load, d_price)

    def min_cost_augmented_rule(m):
        cost_grid = sum(
            m.P_grid_buy[t] * m.p_price[t] - m.P_grid_sell[t] * Config.price_sell
            for t in m.T
        )
        cost_bat = m.E_bat * bat_factor
        obj_main = cost_grid + cost_bat + cost_pv
        carbon_val = sum(m.P_grid_buy[t] for t in m.T) * Config.co2_grid_factor
        # Delta regularization to avoid weakly efficient solutions
        return obj_main + (carbon_val * delta)

    model.Obj_Eco_Aug = Objective(rule=min_cost_augmented_rule, sense=minimize)
    model.C_CarbonLimit = Constraint(
        rule=lambda m: sum(m.P_grid_buy[t] for t in m.T) * Config.co2_grid_factor
        <= target+1.0
    )

    solver = SolverFactory("gurobi")
    solver.options["MIPGap"] = 0.0001
    solver.options["Threads"] = 1
    try:
        res = solver.solve(model, tee=False)
        if res.solver.status == SolverStatus.ok:
            bat_cap = value(model.E_bat)
            cost_run = sum(
                value(model.P_grid_buy[t]) * d_price[t]
                - value(model.P_grid_sell[t]) * Config.price_sell
                for t in model.T
            )
            real_cost = cost_run + bat_cap * bat_factor + cost_pv
            real_carb = (
                sum(value(model.P_grid_buy[t]) for t in model.T)
                * Config.co2_grid_factor
            )

            return {
                "cap": bat_cap,
                "cost": real_cost,
                "carb": real_carb,
                "target": target,
                "ok": True,
            }
        return {"ok": False}
    except:
        return {"ok": False}


# Scenario Running Functions

def run_min_cost(d_pv, d_load, d_price, pv_cap_kW, ratio_roof, ratio_shell):
    """
    Run cost-optimal scenario: minimize total annual cost (grid + battery + PV).
    Returns: (battery_capacity, total_cost, total_carbon, hourly_dataframe)
    """
    model = create_model(d_pv, d_load, d_price)
    bat_factor = get_bat_factor()
    cost_pv = calc_pv_annual_cost(pv_cap_kW, ratio_roof, ratio_shell)

    model.Obj = Objective(
        rule=lambda m: sum(
            m.P_grid_buy[t] * m.p_price[t] - m.P_grid_sell[t] * Config.price_sell
            for t in m.T
        )
        + m.E_bat * bat_factor
        + cost_pv,
        sense=minimize,
    )
    solver = SolverFactory("gurobi")
    solver.options["MIPGap"] = 0.0001
    solver.options["Threads"] = 1

    if solver.solve(model, tee=False).solver.status == SolverStatus.ok:
        bat = value(model.E_bat)
        cost = value(model.Obj)
        carb = sum(value(model.P_grid_buy[t]) for t in model.T) * Config.co2_grid_factor
        print(f"Cost-optimal: Capacity={bat:.1f}, Cost={cost:,.0f}, Carbon={carb:,.0f}")
        return bat, cost, carb, extract_hourly_data(model, d_pv, d_load, d_price)
    return 0, 0, 0, None


def run_min_carbon(
    d_pv, d_load, d_price, pv_cap_kW, ratio_roof, ratio_shell, target_min_carb
):
    """
    Run carbon-optimal scenario:
    1. First minimize carbon emissions to find minimum achievable carbon
    2. Then fix carbon and minimize battery capacity
    Returns: (battery_capacity, total_cost, total_carbon, hourly_dataframe)
    """
    model = create_model(d_pv, d_load, d_price)
    solver = SolverFactory("gurobi")
    solver.options["MIPGap"] = 0.0001
    solver.options["Threads"] = 1

    # Step 1: Minimize carbon emissions
    min_carb = 0.0
    if target_min_carb is not None:
        min_carb = target_min_carb
    else:
        model.Obj_C = Objective(
            rule=lambda m: sum(m.P_grid_buy[t] for t in m.T) * Config.co2_grid_factor,
            sense=minimize,
        )
        if solver.solve(model, tee=False).solver.status == SolverStatus.ok:
                min_carb = value(model.Obj_C)
                model.del_component(model.Obj_C)
        else:
            return 0, 0, 0, None

    # Step 2: Fix carbon emission and minimize capacity
    model.C_Fix = Constraint(
        rule=lambda m: sum(m.P_grid_buy[t] for t in m.T) * Config.co2_grid_factor
        <= min_carb + 1.0
    )
    model.Obj_MinCap = Objective(expr=model.E_bat, sense=minimize)

    if solver.solve(model, tee=False).solver.status == SolverStatus.ok:
        bat = value(model.E_bat)
        bat_factor = get_bat_factor()
        cost_pv = calc_pv_annual_cost(pv_cap_kW, ratio_roof, ratio_shell)
        cost_run = sum(
            value(model.P_grid_buy[t]) * d_price[t]
            - value(model.P_grid_sell[t]) * Config.price_sell
            for t in model.T
        )
        real_cost = cost_run + bat * bat_factor + cost_pv
        print(f"Carbon-optimal: Capacity={bat:.1f}, Cost={real_cost:,.0f}, Carbon={min_carb:.1f}")
        return (
            bat,
            real_cost,
            min_carb,
            extract_hourly_data(model, d_pv, d_load, d_price),
        )
    return 0, 0, 0, None


def run_fixed_capacity(
    d_pv, d_load, d_price, pv_cap_kW, ratio_roof, ratio_shell, target_cap, carbon_cap=None,
):

    model = create_model(d_pv, d_load, d_price)
    bat_factor = get_bat_factor()
    cost_pv = calc_pv_annual_cost(pv_cap_kW, ratio_roof, ratio_shell)

    model.C_FixCap = Constraint(rule=lambda m: m.E_bat == target_cap)
    if carbon_cap is not None:
        model.C_CarbonLimit = Constraint(
            rule=lambda m: sum(m.P_grid_buy[t] for t in m.T) * Config.co2_grid_factor
            <= carbon_cap + 1.0
        )

    model.Obj = Objective(
        rule=lambda m: sum(
            m.P_grid_buy[t] * m.p_price[t] - m.P_grid_sell[t] * Config.price_sell
            for t in m.T
        )
        + m.E_bat * bat_factor
        + cost_pv,
        sense=minimize,
    )
    solver = SolverFactory("gurobi")
    solver.options["MIPGap"] = 0.0001
    solver.options["Threads"] = 1

    if solver.solve(model, tee=False).solver.status == SolverStatus.ok:
        bat = value(model.E_bat)
        cost = value(model.Obj)
        carb = sum(value(model.P_grid_buy[t]) for t in model.T) * Config.co2_grid_factor
        return bat, cost, carb, extract_hourly_data(model, d_pv, d_load, d_price)
    return 0, 0, 0, None

# Pareto Front Scanning via Epsilon-Constraint Method

def run_epsilon_constraint(
    d_pv,
    d_load,
    d_price,
    pv_cap_kW,
    ratio_roof,
    ratio_shell,
    carb_min,
    carb_max,
    cost_min,
    cost_max,
    n_points,
    explicit_boundaries=None,
):
    """
    Generate Pareto front by scanning carbon emission constraints.

    Uses epsilon-constraint method:
    - Carbon emission is constrained as an upper bound
    - Cost is minimized at each carbon level
    - Results in cost-carbon trade-off curve

    Args:
        carb_min, carb_max: Carbon emission range
        cost_min, cost_max: Cost range (for delta calculation)
        n_points: Number of scan points
        explicit_boundaries: Known optimal points to include (cost-optimal, carbon-optimal)

    Returns:
        List of Pareto-efficient solutions with (capacity, cost, carbon)
    """
    n_workers = max(1, os.cpu_count() - 2)

    range_cost = abs(cost_max - cost_min)
    range_carb = abs(carb_max - carb_min)
    range_cost = max(range_cost, 1.0)
    range_carb = max(range_carb, 1.0)
    delta = (range_cost / range_carb) * 1e-4

    # Segmented sampling logic - more points near extremes
    targets = np.array([carb_min, carb_max])
    if n_points > 0:
        n_inner = n_points
        emis_range = carb_max - carb_min

        n1 = int(n_inner * 0.20)
        n2 = int(n_inner * 0.40)
        n3 = n_inner - n1 - n2

        split_1 = carb_min + emis_range * 0.20
        split_2 = carb_min + emis_range * 0.40

        seg1 = np.linspace(carb_min, split_1, n1 + 2)[1:-1]
        seg2 = np.linspace(split_1, split_2, n2 + 2)[1:-1]
        seg3 = np.linspace(split_2, carb_max, n3 + 2)[1:-1]

        targets = np.concatenate(([carb_min], seg1, seg2, seg3, [carb_max]))

    targets = np.unique(targets)
    targets = np.flip(targets)

    bat_factor = get_bat_factor()
    cost_pv = calc_pv_annual_cost(pv_cap_kW, ratio_roof, ratio_shell)

    # Add explicit boundaries to avoid duplicate computation
    raw_results = []
    if explicit_boundaries:
        boundary_carbs = [b["carb"] for b in explicit_boundaries if b]
        # Filter out targets too close to boundaries
        targets = [
            t for t in targets if not any(abs(t - bc) < 1e-3 for bc in boundary_carbs)
        ]

        # Add boundary points directly
        for b in explicit_boundaries:
            if b:
                raw_results.append(
                    {
                        "cap": b["cap"],
                        "cost": b["cost"],
                        "carb": b["carb"],
                        "target": b["carb"],
                        "ok": True,
                    }
                )

    # Compute remaining points in parallel
    tasks = [
        (t, d_pv, d_load, d_price, pv_cap_kW, bat_factor, cost_pv, delta)
        for t in targets
    ]

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_solve_single_epsilon, task) for task in tasks]
        for future in as_completed(futures):
            res = future.result()
            if res["ok"]:
                raw_results.append(res)

    clean = filter_pareto_efficient_with_target(raw_results)
    print(f"Pareto scan complete, valid points: {len(clean)}")
    return clean
