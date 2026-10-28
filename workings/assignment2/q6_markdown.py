from gurobipy import *
import numpy as np

#########Parameters Set-up############

# benchmark price levels and weekly demand estimates
price = np.array([60, 54, 48, 36])
demand = np.array([125, 162.5, 217.5, 348.8])
# salvage value, initial inventory and selling horizon (weeks)
s = 25
I = 2000
T = 15

# price grid with a step of $2 and linearly interpolated demand
price_grid = np.array([60, 58, 56, 54, 52, 50, 48, 46, 44, 42, 40, 38, 36])
demand_grid = np.array([125, 137.5, 150, 162.5, 180.8, 199.1, 217.5,
                        239.4, 261.3, 283.2, 305.1, 327, 348.8])


#########Model Set-up Using Function############
def solve_markdown(price, demand, I, T, full_price_week):
    N = len(price)
    m = Model("Retail")
    m.setParam("OutputFlag", 0)

    # x[i]: number of weeks to offer price level i
    x = m.addVars(N, name="x")

    # sales revenue plus salvage revenue of the leftover inventory
    m.setObjective(quicksum(price[i] * demand[i] * x[i] for i in range(N))
                   + s * (I - quicksum(demand[i] * x[i] for i in range(N))), GRB.MAXIMIZE)

    # capacity constraint: total sales cannot exceed the inventory
    m.addConstr(quicksum(demand[i] * x[i] for i in range(N)) <= I, "capacity")
    # time constraint: total weeks cannot exceed the selling horizon
    m.addConstr(quicksum(x[i] for i in range(N)) <= T, "time")
    # full price constraint
    m.addConstr(x[0] >= full_price_week, "full_price")

    m.optimize()
    weeks = np.array([x[i].X for i in range(N)])
    duals = {c.ConstrName: c.Pi for c in m.getConstrs()}
    return weeks, m.ObjVal, duals


def policy_revenue(weeks, price, demand, I):
    # revenue of a fixed policy, capped by the available inventory
    sales = min(float(np.dot(demand, weeks)), I)
    return float(np.dot(price * demand, weeks)) + s * (I - sales)


def solve():
    res = {}
    # benchmark
    res["benchmark"] = solve_markdown(price, demand, I, T, full_price_week=1)

    # (a) discounts allowed only from week 4: at least 3 weeks at full price
    res["a"] = solve_markdown(price, demand, I, T, full_price_week=3)

    # (b) only 25 units sold in week 1 at $60
    week1_sales = 25
    revenue_week1 = price[0] * week1_sales
    # re-optimize the remaining 14 weeks with the remaining 1975 units;
    # the full price requirement has already been met in week 1
    weeks_b, rev_b, duals_b = solve_markdown(price, demand, I - week1_sales, T - 1, full_price_week=0)
    # stick with the original policy for the remaining 14 weeks
    weeks_orig = res["benchmark"][0].copy()
    weeks_orig[0] -= 1
    rev_stick = revenue_week1 + policy_revenue(weeks_orig, price, demand, I - week1_sales)
    res["b"] = {"weeks": weeks_b, "revenue": revenue_week1 + rev_b,
                "stick_weeks": weeks_orig, "stick_revenue": rev_stick, "duals": duals_b}

    # (c) price grid with 13 price levels
    res["c"] = solve_markdown(price_grid, demand_grid, I, T, full_price_week=1)
    return res


if __name__ == "__main__":
    res = solve()
    print("Benchmark:", np.round(res["benchmark"][0], 4), res["benchmark"][1])
    print("(a):", np.round(res["a"][0], 4), res["a"][1])
    print("(b) adjusted:", np.round(res["b"]["weeks"], 4), res["b"]["revenue"])
    print("(b) stick with original:", res["b"]["stick_revenue"])
    print("(b) improvement:", res["b"]["revenue"] - res["b"]["stick_revenue"])
    print("(c):", np.round(res["c"][0], 4), res["c"][1])
    print("(c) improvement:", res["c"][1] - res["benchmark"][1])
