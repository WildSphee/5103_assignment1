from gurobipy import *
import numpy as np

#########Parameters Set-up############

# pairwise walking time (minutes) between locations 1-6; 1000 on the diagonal forbids self-loops
cost = np.array([[1000,    3,    3,   10,    9,   10],
                 [   3, 1000,    3,    7,    6,    7],
                 [   3,    3, 1000,    7,    6,    7],
                 [  10,    7,    7, 1000,    1,    2],
                 [   9,    6,    6,    1, 1000,    1],
                 [  10,    7,    7,    2,    1, 1000]])

# maximum waiting time of the customers at locations 2-6 (location 1 is the restaurant)
max_wait = np.array([0, 5, 10, 15, 13, 14])

N = cost.shape[0]
M = 1000   # big M


#########Model Set-up############
def model_setup(time_window):
    tsp = Model("tsp_time_window")
    tsp.setParam("OutputFlag", 0)

    x = tsp.addVars(N, N, vtype=GRB.BINARY, name="x")   # 1 if the route goes from i to j
    u = tsp.addVars(N, name="u")                         # arrival time at node i

    tsp.setObjective(quicksum(cost[i, j] * x[i, j] for i in range(N) for j in range(N)), GRB.MINIMIZE)

    # assignment constraints: leave and enter every location exactly once
    tsp.addConstrs((quicksum(x[i, j] for j in range(N)) == 1 for i in range(N)), "out")
    tsp.addConstrs((quicksum(x[i, j] for i in range(N)) == 1 for j in range(N)), "in")

    # accumulated walking time; it also breaks every subtour that avoids location 1
    tsp.addConstr(u[0] == 0, "start")
    tsp.addConstrs((u[i] + cost[i, j] - u[j] <= M * (1 - x[i, j])
                    for i in range(N) for j in range(1, N) if i != j), "time")

    # deliver before the maximum waiting time of each customer
    if time_window:
        tsp.addConstrs((u[j] <= max_wait[j] for j in range(1, N)), "window")
    return tsp, x, u


def route_from(x):
    # follow the arcs with x[i,j] = 1 starting from location 1
    succ = {i: j for i in range(N) for j in range(N) if x[i, j].X > 0.5}
    route, node = [1], 0
    while True:
        node = succ[node]
        route.append(node + 1)
        if node == 0:
            return route


def arrival_times(route):
    t, times = 0, {}
    for a, b in zip(route, route[1:]):
        t += cost[a - 1, b - 1]
        times[b] = t
    return times


def solve(time_window):
    tsp, x, u = model_setup(time_window)
    tsp.optimize()
    if tsp.Status != GRB.OPTIMAL:
        return None
    route = route_from(x)
    return {"time": tsp.ObjVal, "route": route, "arrival": arrival_times(route)}


if __name__ == "__main__":
    for tw in (False, True):
        res = solve(tw)
        print("\nWith time windows:" if tw else "\nWithout time windows:")
        print("Route:", " -> ".join(map(str, res["route"])), " total time:", res["time"])
        print("Arrival times:", res["arrival"])
