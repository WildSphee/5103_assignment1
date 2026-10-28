from gurobipy import *

#########Parameters Set-up############

# price in S$ per 100 g of each fruit
FRUIT, cost = multidict({
    "Apple": 0.5,
    "Banana": 0.3,
    "Blueberries": 2.5,
    "Durian": 10.0,
    "Tangerine": 0.5})

# minimum required and maximum allowed intake of each nutrient
NUTRIENT, out_min, out_max = multidict({
    "Calories": [500, 3000],
    "Carb": [50, 400],
    "Fiber": [20, 30],
    "Vit_A": [2000, 3500],
    "Vit_C": [75, 150]})

# nutrient content per 100 g of each fruit
content = {
    "Apple":       {"Calories": 52,  "Carb": 14, "Fiber": 2.4, "Vit_A": 54,  "Vit_C": 4.6,  "Fat": 0.2},
    "Banana":      {"Calories": 89,  "Carb": 23, "Fiber": 2.6, "Vit_A": 64,  "Vit_C": 8.7,  "Fat": 0.3},
    "Blueberries": {"Calories": 57,  "Carb": 14, "Fiber": 2.4, "Vit_A": 54,  "Vit_C": 9.7,  "Fat": 0.3},
    "Durian":      {"Calories": 147, "Carb": 27, "Fiber": 3.8, "Vit_A": 44,  "Vit_C": 19.7, "Fat": 5.0},
    "Tangerine":   {"Calories": 53,  "Carb": 13, "Fiber": 1.8, "Vit_A": 681, "Vit_C": 26.7, "Fat": 0.3}}

FAT_MIN, FAT_MAX = 0, 10


#########Model Set-up############
def model_setup(with_fat=False):
    nutrients = list(NUTRIENT) + (["Fat"] if with_fat else [])
    lower = {**out_min, "Fat": FAT_MIN}
    upper = {**out_max, "Fat": FAT_MAX}

    m = Model("diet")
    m.setParam("OutputFlag", 0)

    # x[f]: amount of fruit f in units of 100 g
    x = m.addVars(FRUIT, name="x")

    # minimize the total spending
    m.setObjective(quicksum(cost[f] * x[f] for f in FRUIT), GRB.MINIMIZE)

    # nutrient intake must lie between the minimum and the maximum
    m.addConstrs((quicksum(content[f][j] * x[f] for f in FRUIT) >= lower[j] for j in nutrients), "min")
    m.addConstrs((quicksum(content[f][j] * x[f] for f in FRUIT) <= upper[j] for j in nutrients), "max")
    return m, x


def solve(with_fat=False):
    m, x = model_setup(with_fat)
    m.optimize()
    amount = {f: x[f].X for f in FRUIT}
    intake = {j: sum(content[f][j] * amount[f] for f in FRUIT) for j in list(NUTRIENT) + ["Fat"]}
    duals = {c.ConstrName: c.Pi for c in m.getConstrs()}
    return {"amount": amount, "intake": intake, "spend": m.ObjVal, "duals": duals}


if __name__ == "__main__":
    for with_fat in (False, True):
        res = solve(with_fat)
        print("\nWith fat constraint:" if with_fat else "\nOriginal model:")
        for f, v in res["amount"].items():
            print("%-12s %8.2f g" % (f, 100 * v))
        print("Total spending: S$%.4f" % res["spend"])
        print("Fat intake: %.3f g" % res["intake"]["Fat"])
