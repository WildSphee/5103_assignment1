from gurobipy import *
import numpy as np

#########Parameters Set-up############

STORES = ["Jurong West", "Orchard", "Harbour Front"]
N = len(STORES)
price, unit_cost = 100, 50
mu = np.array([300, 500, 500])
sigma = np.array([20, 20, 40])
inventory = np.array([300, 500, 500])
fixed_fee = 200

# unit transshipment cost from store i to store j
ship = np.array([[0, 22, 19],
                 [22, 0, 7],
                 [19, 7, 0]])

DEDICATED = tuplelist([(i, i) for i in range(N)])
TRANSSHIP = tuplelist([(i, j) for i in range(N) for j in range(N)])


def sample_demand(K, seed, sd=sigma):
    # independent normal demands truncated above zero
    rng = np.random.default_rng(seed)
    return np.maximum(rng.normal(mu, sd, size=(K, N)), 0)


#########Second-stage Model: Sales after Demand Is Realized############
def model_setup(ARCS):
    m = Model("multi_location")
    m.setParam("OutputFlag", 0)

    # x[i,j]: units of store i's inventory sold to customers at store j
    x = m.addVars(ARCS, name="x")

    # sales revenue net of transshipment cost
    m.setObjective(quicksum((price - ship[i, j]) * x[i, j] for (i, j) in ARCS), GRB.MAXIMIZE)

    # inventory constraint at each store (right-hand sides are reset later)
    inv_con = m.addConstrs((quicksum(x[i, j] for (i, j) in ARCS.select(i, "*")) <= inventory[i] for i in range(N)), "inventory")
    # demand constraint at each store
    dem_con = m.addConstrs((quicksum(x[i, j] for (i, j) in ARCS.select("*", j)) <= mu[j] for j in range(N)), "demand")
    return m, inv_con, dem_con


def evaluate(ARCS, stock, demand_samples):
    # average second-stage revenue over the demand samples for a given inventory position
    m, inv_con, dem_con = model_setup(ARCS)
    for i in range(N):
        inv_con[i].RHS = stock[i]
    value = np.zeros(len(demand_samples))
    for k, demand in enumerate(demand_samples):
        for j in range(N):
            dem_con[j].RHS = demand[j]
        m.optimize()
        value[k] = m.ObjVal
    return value


#########Sample Average Approximation for the Inventory Positions############
def solve_saa(demand_samples):
    K = len(demand_samples)
    m = Model("SAA")
    m.setParam("OutputFlag", 0)

    # first stage: inventory position at each store
    s = m.addVars(N, name="s")
    # second stage: x[i,j,k] units of store i's stock sold at store j in sample k
    x = m.addVars(N, N, K, name="x")

    m.setObjective(-unit_cost * quicksum(s[i] for i in range(N))
                   + (1.0 / K) * quicksum((price - ship[i, j]) * x[i, j, k]
                                          for i in range(N) for j in range(N) for k in range(K)),
                   GRB.MAXIMIZE)

    m.addConstrs((quicksum(x[i, j, k] for j in range(N)) <= s[i] for i in range(N) for k in range(K)), "inventory")
    m.addConstrs((quicksum(x[i, j, k] for i in range(N)) <= demand_samples[k, j] for j in range(N) for k in range(K)), "demand")
    m.optimize()
    return np.array([s[i].X for i in range(N)]), m.ObjVal


def solve():
    res = {}
    procurement = unit_cost * inventory.sum()

    # (a) expected profit without transshipment
    D = sample_demand(10000, seed=1)
    sales = evaluate(DEDICATED, inventory, D) / price
    res["a"] = {"profit": price * sales.mean() - procurement, "sales": sales.mean(),
                "se": price * sales.std(ddof=1) / np.sqrt(len(D))}

    # (b) no demand uncertainty: demand equals its mean
    sales_det = evaluate(DEDICATED, inventory, mu.reshape(1, -1))
    res["b"] = {"profit": sales_det[0] - procurement}

    # (c) value of transshipment for different sample sizes
    res["c"] = []
    for K in (100, 500, 1000, 5000, 10000):
        D = sample_demand(K, seed=K)
        base = evaluate(DEDICATED, inventory, D)
        trans = evaluate(TRANSSHIP, inventory, D)
        gain = trans - base
        res["c"].append({"K": K, "profit_without": base.mean() - procurement,
                         "profit_with": trans.mean() - procurement - fixed_fee,
                         "gain": gain.mean(), "net": gain.mean() - fixed_fee,
                         "se": gain.std(ddof=1) / np.sqrt(K)})

    # (d) optimal inventory positions under transshipment by SAA
    res["d"] = []
    D_test = sample_demand(10000, seed=2026)
    for K in (50, 100, 200):
        stock, saa_value = solve_saa(sample_demand(K, seed=100 + K))
        test = evaluate(TRANSSHIP, stock, D_test).mean() - unit_cost * stock.sum()
        res["d"].append({"K": K, "stock": stock, "saa": saa_value, "test": test})
    res["d_benchmark"] = evaluate(TRANSSHIP, inventory, D_test).mean() - procurement
    return res


if __name__ == "__main__":
    res = solve()
    print("(a) expected profit: %.2f (expected sales %.2f, s.e. %.2f)" % (res["a"]["profit"], res["a"]["sales"], res["a"]["se"]))
    print("(b) deterministic profit: %.2f" % res["b"]["profit"])
    for r in res["c"]:
        print("(c) K=%5d  gross gain %.2f  net gain %.2f  (s.e. %.2f)" % (r["K"], r["gain"], r["net"], r["se"]))
    for r in res["d"]:
        print("(d) K=%3d  s = %s  SAA value %.2f  out-of-sample profit %.2f"
              % (r["K"], np.round(r["stock"], 2), r["saa"], r["test"]))
    print("(d) out-of-sample profit of (300, 500, 500): %.2f" % res["d_benchmark"])
