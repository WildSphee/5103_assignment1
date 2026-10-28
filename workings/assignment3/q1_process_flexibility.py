from gurobipy import *
import numpy as np

#########Parameters Set-up############

N = 6                               # number of plants and of models
supply = np.full(N, 100)            # weekly capacity at each plant
mean = np.full(N, 100)              # mean demand of each model
cov = np.diag(np.full(N, 30**2))    # independent demands with s.d. 30

DESIGNS = {
    "Dedicated":     tuplelist([(i, i) for i in range(N)]),
    "Open chain":    tuplelist([(i, i) for i in range(N)] + [(i, i + 1) for i in range(N - 1)]),
    "Long chain":    tuplelist([(i, i) for i in range(N)] + [(i, (i + 1) % N) for i in range(N)]),
    "Full flexible": tuplelist([(i, j) for i in range(N) for j in range(N)]),
}


#########Model Set-up Using Function############
def model_setup(ARCS):
    m = Model("Process_Flexi")
    m.setParam("OutputFlag", 0)

    # x[i,j]: amount of model j produced at plant i
    x = m.addVars(ARCS, name="x")

    # maximize total sales
    m.setObjective(quicksum(x[i, j] for (i, j) in ARCS), GRB.MAXIMIZE)

    # capacity constraint at each plant
    m.addConstrs((quicksum(x[i, j] for (i, j) in ARCS.select(i, "*")) <= supply[i] for i in range(N)), "capacity")

    # demand constraint for each model (right-hand side is reset for every sample)
    demand_con = m.addConstrs((quicksum(x[i, j] for (i, j) in ARCS.select("*", j)) <= mean[j] for j in range(N)), "demand")
    return m, demand_con


def evaluate(ARCS, demand_samples):
    m, demand_con = model_setup(ARCS)
    sales = np.zeros(len(demand_samples))
    for k, demand in enumerate(demand_samples):
        for j in range(N):
            demand_con[j].RHS = demand[j]
        m.optimize()
        sales[k] = m.ObjVal
    return sales


def solve(sample_size=1000, seed=5103):
    np.random.seed(seed)
    # demand is sampled from the multivariate normal distribution and truncated above zero;
    # the same samples are used for every design so the designs are compared fairly
    demand_samples = np.maximum(np.random.multivariate_normal(mean, cov, sample_size), 0)
    return {name: evaluate(ARCS, demand_samples) for name, ARCS in DESIGNS.items()}


if __name__ == "__main__":
    for size in (1000, 10000):
        sales = solve(size)
        print("\nSample size", size)
        for name, v in sales.items():
            print("%-14s average sales %.2f (std. error %.2f)" % (name, v.mean(), v.std(ddof=1) / np.sqrt(size)))
