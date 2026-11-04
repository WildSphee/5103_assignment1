<!-- COLUMN 1 -->
## L1 · INTRODUCTION: WHAT OR IS
**In one line:** pick decisions to maximize/minimize an objective subject to constraints, then choose the right tool to solve the model.
**Covered:** course road map LP → network flow → IP → DP. Software: Python + Gurobi, Excel Solver. Application areas: manufacturing, transport, airline/hotel/retail. Cases: **Ford flexible manufacturing** (dedicated vs fully flexible plants; evaluate a design with LP, max flow or simulation); **Uber/Grab** dispatch (greedy matching vs assignment/shortest path), surge pricing (supply–demand model: LP/linear algebra if non-profit, nonlinear if profit-maximizing), **UberPOOL** as a TSP with pickup before drop-off (LP, IP, heuristics); **Rue La La** price optimization (IP/LP); markdown/dynamic pricing (LP, DP).
**Numbers to know:** capacities (100,100,100), demands (20,140,140): dedicated sells 220, full flexibility 300. Dispatch times [2,3;10,20]: greedy 2+20=22 min, optimal 3+10=13.
**Quiz angle:** say which model type fits a story (LP / network / IP / DP) and why.
**Watch out:** greedy, one-step-at-a-time choices can be far from optimal.
## L2 · LINEAR PROGRAMMING & REFORMULATION
**In one line:** write a word problem as a linear model, then rewrite it in a standard form that theory and solvers use.
**Covered:** **Wyndor Glass** prototype: max 3x₁+5x₂; x₁≤4, 2x₂≤12, 3x₁+2x₂≤18, x≥0; solved by the graphical/contour method, optimum (2,6), z=36. Linear algebra review: vectors, matrices, transpose, products, identity, inverse, linear combinations, when A is invertible. General LP with ≥, ≤, = rows → standard form. Tricks: free variables, absolute values, min–max. Regression with L1 / L∞ / L2 error and outlier sensitivity. Sparse recovery (compressed sensing, image reconstruction): min ∑|xⱼ| s.t. Ax=b.
**Formulas:** min cᵀx, Ax=b, x≥0. ≤ row: +slack; ≥ row: −surplus. Free x=x⁺−x⁻. |r|≤t ⇔ −t≤r≤t. L1 and L∞ fits are LPs; L2 is quadratic.
**Quiz angle:** formulate from words; convert to standard form; linearize an absolute-value objective.
**Watch out:** "linear" means linear in the decision variables (no xy, x²). The t≥±r trick needs the objective to push t down.
## L3 · GEOMETRY & THE SIMPLEX METHOD
**In one line:** an LP optimum sits at a corner (BFS); simplex moves from corner to a better adjacent corner until no move helps.
**Covered:** Wyndor in Excel Solver and Gurobi; keep model and data separate. 2-D geometry: feasible region = polyhedron, extreme points, four outcomes (unique, multiple, unbounded, infeasible). Binding constraints and slack. BFS in n dimensions = n linearly independent active constraints. Basic solutions in standard form: pick m columns, set the rest to 0, solve, check ≥0. Degeneracy. Convex sets/functions (local optimum = global). Adjacent BFSs. Simplex: find a BFS → reduced costs → entering variable → ratio test → pivot.
**Formulas:** x_B=B⁻¹b; r_j=c_j−c_BᵀB⁻¹A_j. MIN optimal when all r_j≥0. Example max x₁+x₂; x₁+2x₂≤3, 2x₁+x₂≤3 → (1,1), z=2.
**Quiz angle:** list basic solutions and mark the feasible ones; do one pivot; name binding constraints.
**Watch out:** θ=0 is degeneracy, not infeasibility; the ratio test uses only decreasing variables; an unbounded region ≠ an unbounded objective.
## L4 · DUALITY & SENSITIVITY
**In one line:** every LP has a dual that gives bounds and resource prices; sensitivity asks how the answer moves when data change.
**Covered:** Lagrangian relaxation (min x²+y², x+y=1: g(p)=p−p²/2, best p=1, z=½); LP dual from the Lagrangian; dual of the dual = primal; weak and strong duality; economic view (a market buys Wyndor plant hours at y=(0,1.5,1), value 36 = primal); complementary slackness; what-ifs: add a constraint, add a variable, change a RHS (shadow price + range), change a profit coefficient; Excel and Gurobi sensitivity reports.
**Numbers to know:** plant 3 +1 hour → z=37; +9 hours → z=42, **not** 45 (outside range). Product 1 profit 3→10: old plan alone gains ≥14; new corner (4,3), z=55 (+19).
**Quiz angle:** write a dual; use complementary slackness to get y*; read a shadow price and its valid range.
**Watch out:** shadow prices hold only inside the range and one change at a time; binding does not mean a positive price.
<!-- COLUMN 2 -->
## L5 · LP CASES: MARKDOWN & ROBUST SOURCING
**In one line:** two real LP cases, plus planning for the worst case when data are uncertain.
**Covered:** **markdown management** for seasonal goods (stock fixed before the season; only price can change); data → demand model → optimize; LP in "effective weeks" at each price; effect of initial stock; dynamic adjustment (re-solve with remaining stock and time). **Dual-sourcing drug case:** nominal LP; uncertain raw-material yields; ad-hoc fix; "prepare for the worst" robust LP; box and budgeted uncertainty; duality turns the worst case into linear rows.
**Numbers to know:** markdown optimum 11⅔ weeks at $60 + 3⅓ at $54, revenue $116,750. Drug: nominal profit ≈8,819.66 can miss the ingredient target; robust ≈8,294.57 and switches to raw 1.
**Quiz angle:** formulate the markdown LP; write a robust row (pick the worst coefficient); contrast sensitivity vs uncertainty.
**Watch out:** purchase cost is sunk; with q≥0 in a ≥ row, the worst case uses the **lowest** yields.
## L6 · NETWORK FLOW MODELS
**In one line:** many LPs are flows on a graph; that structure gives integer answers and fast special methods.
**Covered:** graph terms (directed/undirected, path, cycle, acyclic, connected, tree, spanning tree with n−1 arcs, bipartite, complete); min-cost flow (out − in = supply); node–arc incidence matrix; special cases: transportation, assignment, shortest path, max flow; initial solutions by northwest corner or least cost; m+n−1 basic cells form a spanning tree; transportation simplex with potentials. Applications: container shipping between Singapore, Ho Chi Minh and Bangkok (time-expanded network); expediting and outsourcing for a complex machine (project crashing); process flexibility with random demand.
**Formulas:** integer supplies/capacities ⇒ integer optimal flow (TU). Max flow = min cut. Complete graph n(n−1)/2 edges.
**Quiz angle:** write flow-balance rows; build an initial transport BFS; name the special model.
**Watch out:** need ∑b=0; one balance row is redundant; basic arcs can carry zero flow.
## L7 · INTEGER PROGRAMMING
**In one line:** binary and integer variables model yes/no choices and logic; solve with LP relaxation + branch and bound.
**Covered:** MIP, pure IP, BIP; **if-then logic for project selection (Side 4)**; product of binaries; binary × continuous; capital budgeting; facility location; flexibility design with K demand samples; TSP (brute force, subtour cuts, MTZ); UberPOOL pickup/drop-off routing; Sudoku; Rue La La pricing (fix total price k); job scheduling; LP relaxation; Cramer's rule and totally unimodular matrices; branch and bound.
**Numbers to know:** knapsack LP 1150, rounded 950, IP 1000. B&B: root 2090 → optimum 1950.
**Quiz angle:** translate if-then rules; write big-M rows; run a few B&B nodes; explain why rounding fails.
**Watch out:** assignment rows alone allow subtours; use the smallest valid M.
## L8 · DYNAMIC PROGRAMMING
**In one line:** split a sequential problem into stages, summarize the past in a state, and solve backward with the Bellman equation.
**Covered:** deterministic vs stochastic DP; Fibonacci (save sub-results, don't recompute); value function, Bellman equation, boundary; staged shortest path A→J; choosing the state; investment/knapsack with budget as state; Go (~250 moves per state, ~150 per game: far too many states); stochastic two-day newsvendor; open-loop vs adaptive policies; secretary (optimal stopping) with a threshold.
**Numbers to know:** path A→D→F→I→J = 74; knapsack 35; newsvendor profit .4 adaptive vs .35 open-loop; secretary n=4 success 11/24; large n skip ≈37%.
**Quiz angle:** define stage/state/action/transition; fill a DP table; write Bellman with E[·].
**Watch out:** take the expectation **before** the min when you act before demand is seen; infeasible states get ±∞.
