from pyomo.environ import *
from config import Config


def create_model(data_pv, data_load, data_price):
    """
    Create the Pyomo optimization model for battery storage dispatch.

    Decision variables:
        E_bat: Battery capacity (kWh)
        E_init: Initial SOC (kWh)
        P_ch[t]: Charging power at hour t (kW)
        P_dis[t]: Discharging power at hour t (kW)
        P_grid_buy[t]: Grid purchase power at hour t (kW)
        P_grid_sell[t]: Grid sell power at hour t (kW)
        SOC[t]: State of charge at hour t (kWh)
        u_buy[t], u_sell[t]: Binary indicators for buy/sell exclusivity
    """
    model = ConcreteModel()
    model.T = RangeSet(0, Config.hours_total - 1)
    model.p_pv = Param(model.T, initialize=data_pv)
    model.p_load = Param(model.T, initialize=data_load)
    model.p_price = Param(model.T, initialize=data_price)

    # Decision variables
    model.E_bat = Var(domain=NonNegativeReals)  # Battery capacity
    model.E_init = Var(domain=NonNegativeReals)  # Initial SOC
    model.P_ch = Var(model.T, domain=NonNegativeReals)  # Charging power
    model.P_dis = Var(model.T, domain=NonNegativeReals)  # Discharging power
    model.P_grid_buy = Var(model.T, domain=NonNegativeReals)  # Grid purchase
    model.P_grid_sell = Var(model.T, domain=NonNegativeReals)  # Grid sell
    model.SOC = Var(model.T, domain=NonNegativeReals)  # State of charge
    model.u_buy = Var(model.T, domain=Binary)  # Buy indicator
    model.u_sell = Var(model.T, domain=Binary)  # Sell indicator


    # CONSTRAINTS

    # Power balance: Load + Charging + GridSell = PV + Discharging + GridBuy
    def bal_rule(m, t):
        return (
            m.p_load[t] + m.P_ch[t] + m.P_grid_sell[t]
            == m.p_pv[t] + m.P_dis[t] + m.P_grid_buy[t]
        )

    model.C_Bal = Constraint(model.T, rule=bal_rule)

    # SOC evolution: SOC[t] = SOC[t-1] * (1-self_discharge) + P_ch * eff_ch - P_dis / eff_dis
    def soc_rule(m, t):
        prev = m.E_init if t == 0 else m.SOC[t - 1]
        return (
            m.SOC[t]
            == prev * (1 - Config.self_discharge_rate)
            + m.P_ch[t] * Config.eff_ch
            - m.P_dis[t] / Config.eff_dis
        )

    model.C_Soc = Constraint(model.T, rule=soc_rule)

    # Cycle constraint: Final SOC >= Initial SOC (no net drain)
    model.C_Cyc = Constraint(rule=lambda m: m.SOC[Config.hours_total - 1] >= m.E_init)

    # Initial SOC bounds
    model.C_InitMin = Constraint(rule=lambda m: m.E_init >= m.E_bat * Config.soc_min)
    model.C_InitMax = Constraint(rule=lambda m: m.E_init <= m.E_bat * Config.soc_max)

    # No grid charging: PV must supply charging (no grid-to-battery)
    model.C_nogridcharge = Constraint(model.T, rule=lambda m, t: m.P_ch[t] <= m.p_pv[t])

    # No battery-to-grid: PV must supply grid sell (no battery-to-grid)
    model.C_nobatsell = Constraint(
        model.T, rule=lambda m, t: m.P_grid_sell[t] <= m.p_pv[t]
    )

    # Buy/sell mutual exclusion
    tight = max(max(data_load.values()), max(data_pv.values())) * 10.0
    model.C_Mutex = Constraint(model.T, rule=lambda m, t: m.u_buy[t] + m.u_sell[t] <= 1)
    model.C_BuyL = Constraint(
        model.T, rule=lambda m, t: m.P_grid_buy[t] <= m.u_buy[t] * tight
    )
    model.C_SellL = Constraint(
        model.T, rule=lambda m, t: m.P_grid_sell[t] <= m.u_sell[t] * tight
    )

    # Capacity limits: SOC bounds
    model.C_Min = Constraint(
        model.T, rule=lambda m, t: m.SOC[t] >= m.E_bat * Config.soc_min
    )
    model.C_Max = Constraint(
        model.T, rule=lambda m, t: m.SOC[t] <= m.E_bat * Config.soc_max
    )

    # Charging/discharging rate limits
    model.C_Ch = Constraint(
        model.T, rule=lambda m, t: m.P_ch[t] <= m.E_bat * Config.c_rate_ch
    )
    model.C_Dis = Constraint(
        model.T, rule=lambda m, t: m.P_dis[t] <= m.E_bat * Config.c_rate_dis
    )

    return model
