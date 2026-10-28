from gurobipy import *
import numpy as np

#########Parameters Set-up############

d = np.array([3, 2, 3, 2])          # demand in each season
K = np.array([2, 2, 2, 2])          # setup cost (million $)
h = np.array([0.2, 0.2, 0.2, 0.2])  # holding cost per airplane per season (million $)
T = len(d)
M = d.sum()                         # big M: never produce more than the total demand


#########Model Set-up############
def model_setup():
    m = Model("lot_sizing")
    m.setParam("OutputFlag", 0)

    x = m.addVars(T, vtype=GRB.INTEGER, name="x")   # inventory at the end of season t
    y = m.addVars(T, vtype=GRB.INTEGER, name="y")   # airplanes produced in season t
    z = m.addVars(T, vtype=GRB.BINARY, name="z")    # 1 if production is set up in season t

    # setup cost plus holding cost
    m.setObjective(quicksum(K[t] * z[t] + h[t] * x[t] for t in range(T)), GRB.MINIMIZE)

    # inventory balance with zero initial inventory
    m.addConstr(y[0] - x[0] == d[0], "balance[0]")
    m.addConstrs((x[t - 1] + y[t] - x[t] == d[t] for t in range(1, T)), "balance")

    # production is possible only if the facilities are set up
    m.addConstrs((y[t] <= M * z[t] for t in range(T)), "setup")
    return m, x, y, z


def solve():
    m, x, y, z = model_setup()
    # keep every optimal solution in the solution pool to detect ties
    m.setParam("PoolSearchMode", 2)
    m.setParam("PoolSolutions", 50)
    m.setParam("PoolGap", 0)
    m.optimize()

    optimal = []
    for k in range(m.SolCount):
        m.setParam("SolutionNumber", k)
        sol = {"cost": m.PoolObjVal,
               "y": [round(y[t].Xn) for t in range(T)],
               "x": [round(x[t].Xn) for t in range(T)],
               "z": [round(z[t].Xn) for t in range(T)]}
        if abs(sol["cost"] - m.ObjVal) < 1e-6 and all(sol["y"] != s["y"] for s in optimal):
            optimal.append(sol)
    return optimal[0], optimal


if __name__ == "__main__":
    best, alternatives = solve()
    print("Minimum total cost: %.2f million" % best["cost"])
    for sol in alternatives:
        print("production", sol["y"], "inventory", sol["x"], "setup", sol["z"])
