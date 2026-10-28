#!/usr/bin/env python3
"""Solve DBA5103 Assignment 2 and generate the DOCX submission.

Questions 5 and 6 are solved with the Gurobi models in ``workings/assignment2``,
whose source is attached verbatim in the code appendix. The analytical answers
to Questions 1 to 4 are re-checked numerically before the document is written.
"""

from __future__ import annotations

import itertools
import shutil
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linprog

from assignment2 import q5_diet, q6_markdown
from submission_common import (
    ROOT,
    add_ai_declaration,
    add_answer_box,
    add_code_block,
    add_figure,
    add_formula,
    add_text,
    make_table,
    new_document,
    render_formula,
    render_matrix,
    save_document,
)

OUTPUT_FILE = ROOT / "DBA5103 Assignment 2 CHAN HIU LOK.docx"
CODE_DIR = Path(__file__).resolve().parent / "assignment2"


def fmt_money(value: float) -> str:
    return f"${value:,.0f}" if abs(value - round(value)) < 0.005 else f"${value:,.2f}"


def vertices(G: np.ndarray, h: np.ndarray):
    """Enumerate the extreme points of {x : Gx <= h} by brute force."""
    n = G.shape[1]
    found = set()
    for rows in itertools.combinations(range(len(G)), n):
        B = G[list(rows)]
        if abs(np.linalg.det(B)) < 1e-9:
            continue
        x = np.linalg.solve(B, h[list(rows)])
        if np.all(G @ x <= h + 1e-9):
            found.add(tuple(float(v) for v in np.round(x, 9) + 0.0))
    return found


def verify_analytical_answers() -> dict:
    """Numerical checks of Questions 1, 3 and 4."""
    # 1(a): x1 + x2 + x3/2 <= 1, x >= 0 in R^4
    G = np.vstack([[1, 1, 0.5, 0], -np.eye(4)])
    h = np.array([1, 0, 0, 0, 0], float)
    assert vertices(G, h) == {(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 2, 0)}

    # 1(b)
    G = np.array([[1, -1, 0], [0, 1, -1], [0, 0, 1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]], float)
    h = np.array([1, 1, 1, 0, 0, 0], float)
    expected_b = {(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 2, 1), (1, 0, 0), (1, 0, 1), (2, 1, 0), (3, 2, 1)}
    assert vertices(G, h) == expected_b

    # 1(c): basic feasible solutions of Ax = b, x >= 0
    A = np.array([[1, 0, 1, 1], [0, 1, 0, 1], [0, 0, 0, 1]], float)
    b = np.array([2, 2, 1], float)
    bfs = set()
    for basis in itertools.combinations(range(4), 3):
        B = A[:, basis]
        if abs(np.linalg.det(B)) < 1e-9:
            continue
        x = np.zeros(4)
        x[list(basis)] = np.linalg.solve(B, b)
        if np.all(x >= -1e-9):
            bfs.add(tuple(float(v) for v in np.round(x, 9) + 0.0))
    assert bfs == {(1, 1, 0, 1), (0, 1, 1, 1)}

    # 3: primal and dual optimal values coincide
    A3 = np.array([[1, 2, 2], [2, 1, 2], [2, 2, 1]], float)
    primal = linprog(-np.array([10, 12, 12]), A_ub=A3, b_ub=[20, 20, 20], method="highs")
    dual = linprog([20, 20, 20], A_ub=-A3.T, b_ub=-np.array([10, 12, 12]), method="highs")
    assert np.allclose(primal.x, [4, 4, 4]) and np.allclose(dual.x, [3.6, 1.6, 1.6])
    assert np.isclose(-primal.fun, 136) and np.isclose(dual.fun, 136)

    # 4: base model, extra clay, and relaxed Primrose constraint
    c = -np.array([51, 102, 66, 66, 89], float)
    A4 = [[10, 15, 10, 10, 20], [1, 2, 2, 1, 1], [3, 1, 6, 6, 3], [2, 4, 2, 5, 3]]
    b4 = [130, 13, 45, 23]
    base = linprog(c, A_ub=A4, b_ub=b4, A_eq=[[0, 0, 1, -1, 0]], b_eq=[0], method="highs")
    clay = linprog(c, A_ub=A4, b_ub=[150, 13, 45, 23], A_eq=[[0, 0, 1, -1, 0]], b_eq=[0], method="highs")
    relaxed = linprog(c, A_ub=A4 + [[0, 0, -1, 1, 0]], b_ub=b4 + [0], method="highs")
    assert np.allclose(base.x, [0, 2, 0, 0, 5]) and np.isclose(-base.fun, 649)
    assert np.isclose(-clay.fun - (-base.fun), 20 / 0.7, atol=1e-6)
    assert relaxed.x[2] > 1e-6
    return {"clay_profit": -clay.fun, "relaxed": relaxed.x, "relaxed_profit": -relaxed.fun}


def plot_markdown(path: Path, md) -> None:
    labels = ["Benchmark", "Week-1 shock,\nre-optimized", "$2 price grid"]
    policies = [
        (q6_markdown.price, md["benchmark"][0]),
        (q6_markdown.price, np.r_[1 + md["b"]["weeks"][0], md["b"]["weeks"][1:]]),
        (q6_markdown.price_grid, md["c"][0]),
    ]
    colors = {60: "#18354A", 58: "#4C7A99", 54: "#8FB3C9", 48: "#C8D6DE", 36: "#E4EBEF"}
    fig, ax = plt.subplots(figsize=(6.4, 2.6), dpi=240)
    used = set()
    for row, (prices, weeks) in enumerate(policies):
        left = 0.0
        for p, w in zip(prices, weeks):
            if w < 1e-6:
                continue
            color = colors.get(int(p), "#B0BEC5")
            label = f"${int(p)}" if int(p) not in used else None
            used.add(int(p))
            ax.barh(row, w, left=left, color=color, label=label, edgecolor="white")
            text_color = "white" if int(p) in (60, 58) else "#111820"
            ax.text(left + w / 2, row, f"{w:.2f} wk" if abs(w - round(w)) > 1e-6 else f"{w:.0f} wk",
                    ha="center", va="center", fontsize=8, color=text_color)
            left += w
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 15)
    ax.set_xlabel("Weeks in the 15-week season")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.2)
    handles, names = ax.get_legend_handles_labels()
    order = sorted(range(len(names)), key=lambda k: -int(names[k][1:]))
    ax.legend([handles[k] for k in order], [names[k] for k in order],
              frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_question_1(doc, image_dir: Path) -> None:
    doc.add_heading("1. Extreme Points of Polyhedra", level=1)
    add_text(
        doc,
        "Every part uses the same characterisation. A point of a polyhedron in n dimensions is an extreme point exactly when it is feasible and n linearly independent constraints are binding there. For a polyhedron written in standard form, Ax = b and x >= 0, this is the same as a basic feasible solution: choose linearly independent columns of A as a basis, set the remaining variables to zero, solve for the basic variables, and keep the solution if it is nonnegative.",
    )

    doc.add_heading("1(a) Budget-type constraint in four variables", level=2)
    add_text(
        doc,
        "The polyhedron lives in four dimensions and has five constraints: the budget-type row and the four sign restrictions. The variable x4 appears in no constraint other than its own sign restriction. If x4 were positive, the point could be moved a little up and a little down in the x4 direction without leaving the set, so it would be the midpoint of two feasible points and could not be extreme. Every extreme point therefore has x4 = 0, and the other three binding constraints must be chosen from the remaining four.",
    )
    make_table(
        doc,
        ["Binding constraints (besides x4 = 0)", "Solution", "Feasible?"],
        [
            ["x1 = 0, x2 = 0, x3 = 0", "(0, 0, 0, 0)", "Yes"],
            ["x1 + x2 + x3/2 = 1, x2 = 0, x3 = 0", "(1, 0, 0, 0)", "Yes"],
            ["x1 + x2 + x3/2 = 1, x1 = 0, x3 = 0", "(0, 1, 0, 0)", "Yes"],
            ["x1 + x2 + x3/2 = 1, x1 = 0, x2 = 0", "(0, 0, 2, 0)", "Yes"],
        ],
        widths=[3.0, 1.45, 0.95],
        font_size=8.3,
    )
    add_answer_box(doc, "Answer", "The extreme points are (0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0) and (0, 0, 2, 0).")
    add_text(
        doc,
        "The set is unbounded along the x4 axis, but that does not create further extreme points; it only means that the polyhedron contains a ray in addition to the four corners.",
    )

    doc.add_heading("1(b) Chain of difference constraints", level=2)
    add_text(
        doc,
        "Three binding constraints are needed in three dimensions. The six constraints split naturally into three pairs, one for each variable:",
    )
    p = image_dir / "q1b_pairs.png"
    render_formula(
        p,
        [
            r"$\{x_1\geq0,\ x_1-x_2\leq1\},\qquad \{x_2\geq0,\ x_2-x_3\leq1\},\qquad \{x_3\geq0,\ x_3\leq1\}.$",
        ],
        fontsize=15.0,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "The two constraints of a pair can never bind together. If x1 = 0 and x1 - x2 = 1, then x2 = -1, which is infeasible; the same happens for the second pair, and x3 cannot equal both 0 and 1. Three binding constraints must therefore consist of exactly one constraint from each pair. Such a system is triangular, so it is always linearly independent, and it can be solved from x3 upwards:",
    )
    p = image_dir / "q1b_recursion.png"
    render_formula(
        p,
        [r"$x_3\in\{0,\,1\},\qquad x_2\in\{0,\ x_3+1\},\qquad x_1\in\{0,\ x_2+1\}.$"],
        fontsize=15.5,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "All eight choices are feasible. When a variable is set to zero, the other constraint of its pair reads minus the next variable <= 1, which holds because every variable is nonnegative; when a difference constraint is chosen, the variable equals the next one plus one and is positive. The eight extreme points are:",
    )
    make_table(
        doc,
        ["x3 from", "x2 from", "x1 from", "Extreme point"],
        [
            ["x3 = 0", "x2 = 0", "x1 = 0", "(0, 0, 0)"],
            ["x3 = 0", "x2 = 0", "x1 - x2 = 1", "(1, 0, 0)"],
            ["x3 = 0", "x2 - x3 = 1", "x1 = 0", "(0, 1, 0)"],
            ["x3 = 0", "x2 - x3 = 1", "x1 - x2 = 1", "(2, 1, 0)"],
            ["x3 = 1", "x2 = 0", "x1 = 0", "(0, 0, 1)"],
            ["x3 = 1", "x2 = 0", "x1 - x2 = 1", "(1, 0, 1)"],
            ["x3 = 1", "x2 - x3 = 1", "x1 = 0", "(0, 2, 1)"],
            ["x3 = 1", "x2 - x3 = 1", "x1 - x2 = 1", "(3, 2, 1)"],
        ],
        widths=[1.15, 1.3, 1.3, 1.35],
        font_size=8.3,
    )
    add_answer_box(doc, "Answer", "(0, 0, 0), (1, 0, 0), (0, 1, 0), (2, 1, 0), (0, 0, 1), (1, 0, 1), (0, 2, 1) and (3, 2, 1).")

    doc.add_heading("1(c) Polyhedron in standard form", level=2)
    add_text(
        doc,
        "The three rows of A are linearly independent, so every basic solution has three basic variables and one nonbasic variable set to zero. The columns are:",
    )
    p = image_dir / "q1c_columns.png"
    render_formula(
        p,
        [r"$A_1=(1,0,0)^{\mathsf{T}},\quad A_2=(0,1,0)^{\mathsf{T}},\quad A_3=(1,0,0)^{\mathsf{T}},\quad A_4=(1,1,1)^{\mathsf{T}}.$"],
        fontsize=15.0,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "Because the first and third columns are identical, no basis can contain both of them, which leaves only two of the four possible bases:",
    )
    make_table(
        doc,
        ["Basis", "Nonbasic variable", "Solution of Ax = b", "Status"],
        [
            ["{A1, A2, A3}", "x4 = 0", "singular (A1 = A3)", "not a basis"],
            ["{A1, A3, A4}", "x2 = 0", "singular (A1 = A3)", "not a basis"],
            ["{A1, A2, A4}", "x3 = 0", "(1, 1, 0, 1)", "basic feasible"],
            ["{A2, A3, A4}", "x1 = 0", "(0, 1, 1, 1)", "basic feasible"],
        ],
        widths=[1.2, 1.3, 1.6, 1.2],
        font_size=8.3,
    )
    add_answer_box(doc, "Answer", "The extreme points are (1, 1, 0, 1) and (0, 1, 1, 1).")
    add_text(
        doc,
        "The equations fix x4 = 1 and x2 = 1 and leave only x1 + x3 = 1, so the polyhedron is the line segment joining the two extreme points, which is consistent with finding exactly two of them.",
    )


def add_question_2(doc, image_dir: Path) -> None:
    doc.add_heading("2. Portfolio Management", level=1)
    doc.add_heading("2(a) Dual problem", level=2)
    add_text(
        doc,
        "The primal is a maximization with a single less-than-or-equal constraint and nonnegative variables. Its dual therefore has one nonnegative variable p, attached to the budget, and one greater-than-or-equal constraint for each stock:",
    )
    p = image_dir / "q2_dual.png"
    render_formula(
        p,
        [
            r"$\min_{p}\quad b\,p$",
            r"$\mathrm{s.t.}\quad p\geq r_i,\quad i=1,\ldots,100,\qquad p\geq0.$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "In economic terms p is the price of one dollar of budget. The dual constraints say that this price must be at least the return on every stock, so that no stock offers an arbitrage opportunity at that price.",
    )

    doc.add_heading("2(b) Optimal primal and dual solutions", level=2)
    add_text(
        doc,
        "Let i* be a stock with the largest expected return, r* = max r_i. The feasible set of the primal is a simplex whose extreme points are investing nothing or investing the entire budget in a single stock. Comparing these extreme points gives:",
    )
    p = image_dir / "q2_primal.png"
    render_formula(
        p,
        [
            r"$r^{*}>0:\qquad x_{i^{*}}^{*}=b,\quad x_j^{*}=0\ (j\neq i^{*}),\qquad \mathrm{objective}=b\,r^{*},$",
            r"$r^{*}\leq0:\qquad x^{*}=0,\qquad \mathrm{objective}=0.$",
        ],
        fontsize=15.5,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "In the dual the objective b p is increasing in p because b > 0, so p should be as small as the constraints allow, namely the larger of the best return and zero:",
    )
    p = image_dir / "q2_dual_opt.png"
    render_formula(p, [r"$p^{*}=\max\{r^{*},\,0\},\qquad \mathrm{objective}=b\,\max\{r^{*},\,0\}.$"])
    add_formula(doc, p)

    doc.add_heading("2(c) Verification through weak duality", level=2)
    add_text(doc, "For any primal feasible x and any dual feasible p, the dual constraints and then the budget constraint give:")
    p = image_dir / "q2_weak.png"
    render_formula(
        p,
        [
            r"$\sum_{i=1}^{100}r_ix_i\ \leq\ \sum_{i=1}^{100}p\,x_i\ =\ p\sum_{i=1}^{100}x_i\ \leq\ p\,b.$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "The first inequality uses r_i <= p together with x_i >= 0, and the second uses p >= 0 together with the budget. Every primal objective value is therefore a lower bound on every dual objective value. The solutions in (b) are feasible and both attain b max{r*, 0}, so no primal solution can do better and no dual solution can do lower: both are optimal.",
    )
    add_answer_box(
        doc,
        "Check",
        "The pair also satisfies complementary slackness. When r* > 0 the budget is binding and p* > 0, and the only positive investment is in stock i*, whose dual constraint p* >= r_i* is binding. When r* <= 0 nothing is invested and the budget constraint has p* = 0.",
    )


def add_question_3(doc, image_dir: Path) -> None:
    doc.add_heading("3. Duality and Complementary Slackness", level=1)
    doc.add_heading("3(a) Dual problem", level=2)
    add_text(doc, "Attaching a nonnegative price to each of the three resource constraints gives the dual:")
    p = image_dir / "q3_dual.png"
    render_formula(
        p,
        [
            r"$\min\quad 20p_1+20p_2+20p_3$",
            r"$\mathrm{s.t.}\quad p_1+2p_2+2p_3\geq10,$",
            r"$2p_1+p_2+2p_3\geq12,$",
            r"$2p_1+2p_2+p_3\geq12,\qquad p_1,p_2,p_3\geq0.$",
        ],
    )
    add_formula(doc, p)

    doc.add_heading("3(b) Dual solution from complementary slackness", level=2)
    add_text(doc, "The complementary slackness conditions pair every constraint with the variable of the other problem:")
    p = image_dir / "q3_cs.png"
    render_formula(
        p,
        [r"$p_i\,(b_i-a_i^{\mathsf{T}}x)=0,\qquad x_j\,(p^{\mathsf{T}}A_j-c_j)=0.$"],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "At x = (4, 4, 4) all three primal variables are positive, so all three dual constraints must be binding. This gives a system of three equations:",
    )
    p = image_dir / "q3_system.png"
    render_formula(
        p,
        [
            r"$p_1+2p_2+2p_3=10,\qquad 2p_1+p_2+2p_3=12,\qquad 2p_1+2p_2+p_3=12.$",
            r"$\Longrightarrow\quad p_1-p_2=2,\quad p_1-p_3=2\quad\Longrightarrow\quad 5p_1-8=10.$",
        ],
        fontsize=15.2,
    )
    add_formula(doc, p)
    p = image_dir / "q3_solution.png"
    render_formula(p, [r"$p^{*}=(p_1,p_2,p_3)=\left(\frac{18}{5},\ \frac{8}{5},\ \frac{8}{5}\right)=(3.6,\ 1.6,\ 1.6).$"])
    add_formula(doc, p)
    add_answer_box(
        doc,
        "Check",
        "The solution is nonnegative, so it is dual feasible. Each primal constraint is binding at x = (4, 4, 4) (every row sums to 20), so the first set of conditions holds as well. Both objectives equal 136: 10(4) + 12(4) + 12(4) = 136 and 20(3.6 + 1.6 + 1.6) = 136, confirming optimality.",
    )


def add_question_4(doc, image_dir: Path, checks) -> None:
    doc.add_heading("4. Sensitivity Analysis for Pottery Production", level=1)
    doc.add_heading("4(a) Optimal production plan", level=2)
    add_text(
        doc,
        "From Table 2.2, the plan is to make 2 Currier sets and 5 Bluetail sets and none of the others. The total profit is 102(2) + 89(5) = $649. Checking the resources at this plan shows which constraints are binding:",
    )
    make_table(
        doc,
        ["Constraint", "Usage at optimum", "Capacity", "Slack", "Dual value"],
        [
            ["Clay (lbs)", "15(2) + 20(5) = 130", "130", "0", "1.429"],
            ["Enamel (lbs)", "2(2) + 1(5) = 9", "13", "4", "0"],
            ["Dry room (hours)", "1(2) + 3(5) = 17", "45", "28", "0"],
            ["Kiln (hours)", "4(2) + 3(5) = 23", "23", "0", "20.143"],
            ["Primrose methods", "P1 - P2 = 0", "0", "0", "11.429"],
        ],
        widths=[1.35, 1.55, 0.8, 0.6, 0.9],
        font_size=8.2,
    )
    add_answer_box(
        doc,
        "Answer",
        "E = 0, C = 2, P1 = 0, P2 = 0, B = 5, with a total profit of $649. By strong duality the dual objective agrees: 130(1.429) + 23(20.143) = 649.",
    )
    add_text(
        doc,
        "Complementary slackness explains the pattern of the dual values. Enamel and dry room time are left over, so their prices are zero; clay and kiln time are used up, so their prices can be positive.",
    )

    doc.add_heading("4(b) Economic interpretation of the dual variables", level=2)
    add_text(
        doc,
        "A dual variable is the shadow price of its constraint: the change in optimal profit when the right-hand side increases by one unit, valid while the change stays within the allowable range in Table 2.3. It is also the most the manufacturer should be willing to pay for one more unit of the resource.",
    )
    make_table(
        doc,
        ["Constraint", "Shadow price", "Interpretation", "Valid range of RHS"],
        [
            ["Clay", "$1.429 per lb", "Each extra pound of clay raises profit by about $1.43.", "86.25 to 153.33 lbs"],
            ["Enamel", "$0", "4 lbs are unused, so more enamel adds nothing.", "at least 9 lbs"],
            ["Dry room", "$0", "28 hours are idle, so more dry-room time adds nothing.", "at least 17 hours"],
            ["Kiln", "$20.143 per hour", "Kiln time is the most valuable bottleneck.", "19.5 to 28.6 hours"],
            ["Primrose", "$11.429 per set", "Cost of the equal-methods commitment: every extra Primrose set made by method 1 rather than method 2 would raise profit by $11.43.", "P1 - P2 from 0 to 3.5"],
        ],
        widths=[0.85, 1.05, 2.85, 1.25],
        font_size=7.9,
    )

    doc.add_heading("4(c) Buying 20 additional pounds of clay", level=2)
    add_text(
        doc,
        "The increase of 20 lbs is within the allowable increase of 23.33 lbs, so the shadow price of $1.429 applies to the whole purchase. The extra clay is worth 20 x 1.429 = $28.57 in additional profit, against a purchase cost of 20 x $1.10 = $22.00.",
    )
    add_answer_box(
        doc,
        "Answer",
        f"Yes. The net gain is about $6.57. Re-solving the model with 150 lbs of clay confirms a profit of ${checks['clay_profit']:,.2f}, which is $28.57 above $649.",
    )

    doc.add_heading("4(d) Relaxing the Primrose constraint to P1 - P2 >= 0", level=2)
    add_text(
        doc,
        "The relaxed constraint is the same as P1 - P2 = d with any d >= 0. The shadow price of the original constraint is +11.429 with an allowable increase of 3.5, so raising d from 0 increases profit by $11.429 per unit, at least up to d = 3.5. The relaxed model therefore prefers a positive d, and P1 = P2 + d >= d > 0.",
    )
    add_text(
        doc,
        "The same conclusion follows from the sign of the dual variable. In a maximization problem a greater-than-or-equal constraint must have a nonpositive dual price at an optimum. The current dual price of +11.429 has the wrong sign, so the old plan is no longer optimal once the constraint becomes an inequality, and the improvement comes from making more Primrose by method 1.",
    )
    x = checks["relaxed"]
    add_answer_box(
        doc,
        "Answer",
        f"Yes, Primrose made by method 1 becomes positive. Re-solving the relaxed model gives P1 = {x[2]:.1f}, P2 = {x[3]:.0f}, C = {x[1]:.0f}, B = {x[4]:.0f} and a profit of ${checks['relaxed_profit']:,.0f}. The increase of $40 equals 3.5 x 11.429, the shadow price applied over the full allowable increase.",
    )


def add_question_5(doc, image_dir: Path, diet, diet_fat) -> None:
    doc.add_heading("5. Diet Problem", level=1)
    doc.add_heading("5(a) Model, solution and interpretation", level=2)
    add_text(
        doc,
        "Let x_f be the amount of fruit f bought, in units of 100 g, let c_f be its price and let a_jf be the amount of nutrient j in 100 g of fruit f. The cheapest diet within the intake limits L_j and U_j solves the linear program:",
    )
    p = image_dir / "q5_model.png"
    render_formula(
        p,
        [
            r"$\min\quad \sum_{f}c_fx_f$",
            r"$\mathrm{s.t.}\quad L_j\leq\sum_{f}a_{jf}x_f\leq U_j,\qquad j\in\{\mathrm{Cal.,\ Carb.,\ Fiber,\ Vit.\,A,\ Vit.\,C}\},$",
            r"$x_f\geq0,\qquad f\in\{\mathrm{Apple,\ Banana,\ Blueberries,\ Durian,\ Tangerine}\}.$",
        ],
        fontsize=14.8,
    )
    add_formula(doc, p)
    add_text(doc, "Solving the model with Gurobi (code in the appendix) gives the following purchase plan and nutrient intake:")
    make_table(
        doc,
        ["Fruit", "Amount", "Cost"],
        [[f, f"{100 * v:,.2f} g", f"S${q5_diet.cost[f] * v:,.4f}"] for f, v in diet["amount"].items() if v > 1e-9]
        + [[", ".join(f for f, v in diet["amount"].items() if v <= 1e-9), "0 g", "S$0"]]
        + [["Total", f"{100 * sum(diet['amount'].values()):,.2f} g", f"S${diet['spend']:,.4f}"]],
        widths=[1.6, 1.3, 1.3],
        font_size=8.3,
    )
    names = {"Calories": "Calories", "Carb": "Carbohydrate (g)", "Fiber": "Fiber (g)", "Vit_A": "Vitamin A (IU)", "Vit_C": "Vitamin C (mg)"}
    rows = []
    for j in q5_diet.NUTRIENT:
        v = diet["intake"][j]
        lo, hi = q5_diet.out_min[j], q5_diet.out_max[j]
        status = "at minimum" if abs(v - lo) < 1e-6 else ("at maximum" if abs(v - hi) < 1e-6 else "within limits")
        rows.append([names[j], f"{v:,.2f}", f"{lo:,} to {hi:,}", status])
    make_table(doc, ["Nutrient", "Intake", "Allowed range", "Status"], rows, widths=[1.6, 1.0, 1.45, 1.2], font_size=8.3)
    fiber_dual = diet["duals"]["min[Fiber]"]
    vita_dual = diet["duals"]["min[Vit_A]"]
    add_answer_box(
        doc,
        "Answer",
        f"Buy about 605 g of banana and 237 g of tangerine, for a total of S${diet['spend']:.2f}. Apples, blueberries and durian are not bought.",
    )
    add_text(
        doc,
        f"Only two constraints are binding, the minimum fiber and the minimum vitamin A requirements, and two foods are bought. This is the extreme-point structure one would expect: two binding requirements pin down the two positive amounts. Banana is the cheapest source of fiber at S$0.30 for 2.6 g, and tangerine is by far the richest source of vitamin A, so together they meet both binding requirements at the lowest cost, and every other nutrient then comes out within its limits. The shadow prices show what tightening the binding requirements would cost: about S${fiber_dual:.3f} for each extra gram of fiber and S${vita_dual * 100:.3f} for each extra 100 IU of vitamin A.",
    )

    doc.add_heading("5(b) Adding a limit on fat intake", level=2)
    add_text(
        doc,
        "The fat content of the current optimal diet can be read off without solving anything new:",
    )
    a = diet["amount"]
    p = image_dir / "q5_fat.png"
    render_formula(
        p,
        [
            rf"$0.3\times{a['Banana']:.4f}+0.3\times{a['Tangerine']:.4f}={diet['intake']['Fat']:.3f}\ \mathrm{{g}}\ \in[0,\,10].$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "Adding a constraint can only shrink the feasible set, so the minimum cost cannot fall. The current optimal diet, however, already satisfies the new constraint, so it is still feasible and therefore still optimal.",
    )
    add_answer_box(
        doc,
        "Answer",
        f"Neither the diet nor the spending changes: still about 605 g of banana and 237 g of tangerine for S${diet['spend']:.2f}. Re-solving with the fat constraint confirms S${diet_fat['spend']:.2f} and the same amounts.",
    )


def add_question_6(doc, image_dir: Path, md) -> None:
    doc.add_heading("6. Markdown Management", level=1)
    add_text(
        doc,
        "Let x_i be the number of weeks price p_i is offered, D_i the weekly demand at that price, I the inventory, T the season length and s the salvage value. The benchmark model maximizes sales plus salvage revenue:",
    )
    p = image_dir / "q6_model.png"
    render_formula(
        p,
        [
            r"$\max\quad \sum_{i}p_iD_ix_i+s\left(I-\sum_{i}D_ix_i\right)$",
            r"$\mathrm{s.t.}\quad \sum_{i}D_ix_i\leq I,\qquad \sum_{i}x_i\leq T,\qquad x_1\geq1,\qquad x_i\geq0.$",
        ],
    )
    add_formula(doc, p)
    weeks, rev, _ = md["benchmark"]
    add_text(
        doc,
        f"With I = 2,000, T = 15 and s = $25, the solution is {weeks[0]:.2f} weeks at $60 followed by {weeks[1]:.2f} weeks at $54, with revenue {fmt_money(rev)}. Both the inventory and the time constraints are binding, while the full-price constraint is not.",
    )

    doc.add_heading("6(a) Discounts allowed only from week 4", level=2)
    weeks_a, rev_a, _ = md["a"]
    add_text(
        doc,
        "Discounting from week 4 onwards means that the first three weeks must be at full price, so the full-price constraint becomes x1 >= 3. The benchmark solution already uses full price for 11.67 weeks, so it satisfies the new constraint. A constraint that is not binding at the optimum can be tightened up to its current slack without changing the solution; the shadow price of the full-price constraint is zero.",
    )
    add_answer_box(
        doc,
        "Answer",
        f"No. The retailer keeps the same strategy, {weeks_a[0]:.2f} weeks at $60 and then {weeks_a[1]:.2f} weeks at $54, and still earns {fmt_money(rev_a)}.",
    )

    doc.add_heading("6(b) Re-optimizing after a weak first week", level=2)
    b = md["b"]
    add_text(
        doc,
        "After week 1 only 25 units have been sold, so 1,975 units and 14 weeks remain, and the full-price requirement has already been met. The retailer should treat this as a new starting point and re-solve the model with I = 1,975, T = 14 and no full-price constraint, adding back the $1,500 already earned in week 1.",
    )
    make_table(
        doc,
        ["Policy for weeks 2 to 15", "Weeks at $60", "Weeks at $54", "Units sold", "Units salvaged", "Total revenue"],
        [
            [
                "Keep the original plan",
                f"{b['stick_weeks'][0]:.2f}",
                f"{b['stick_weeks'][1]:.2f}",
                f"{np.dot(q6_markdown.demand, b['stick_weeks']):,.0f}",
                f"{1975 - np.dot(q6_markdown.demand, b['stick_weeks']):,.0f}",
                fmt_money(b["stick_revenue"]),
            ],
            [
                "Re-optimized plan",
                f"{b['weeks'][0]:.2f}",
                f"{b['weeks'][1]:.2f}",
                f"{np.dot(q6_markdown.demand, b['weeks']):,.0f}",
                f"{1975 - np.dot(q6_markdown.demand, b['weeks']):,.0f}",
                fmt_money(b["revenue"]),
            ],
        ],
        widths=[1.55, 0.85, 0.85, 0.8, 0.95, 1.05],
        font_size=8.0,
    )
    gain = b["revenue"] - b["stick_revenue"]
    add_answer_box(
        doc,
        "Answer",
        f"The retailer should cut the remaining full-price period to {b['weeks'][0]:.0f} weeks (9 weeks in total including week 1) and then sell at $54 for {b['weeks'][1]:.0f} weeks. Revenue rises from {fmt_money(b['stick_revenue'])} to {fmt_money(b['revenue'])}, an improvement of {fmt_money(gain)} or {100 * gain / b['stick_revenue']:.2f}%.",
    )
    add_text(
        doc,
        "The weak first week leaves 100 more units on hand than the original plan expected. Keeping the original plan would send those units to the outlet at $25, whereas the re-optimized plan starts the $54 markdown earlier and sells the whole remaining stock. The case shows the value of updating the plan as information arrives rather than fixing the markdown schedule at the start of the season.",
    )

    doc.add_heading("6(c) Finer price grid", level=2)
    weeks_c, rev_c, _ = md["c"]
    used = [(q6_markdown.price_grid[i], w) for i, w in enumerate(weeks_c) if w > 1e-6]
    add_text(
        doc,
        "With the thirteen-level price grid the model is unchanged except that the price and demand vectors are replaced by those of Table 2.6. Solving it gives:",
    )
    make_table(
        doc,
        ["Model", "Policy", "Revenue", "Change vs benchmark"],
        [
            ["Benchmark (4 prices)", f"{weeks[0]:.2f} wk at $60, then {weeks[1]:.2f} wk at $54", fmt_money(rev), "-"],
            [
                "Price grid (13 prices)",
                ", then ".join(f"{w:.0f} wk at ${p:.0f}" for p, w in used),
                fmt_money(rev_c),
                f"+{fmt_money(rev_c - rev)} (+{100 * (rev_c - rev) / rev:.2f}%)",
            ],
        ],
        widths=[1.45, 2.55, 0.95, 1.3],
        font_size=8.1,
    )
    plot_path = image_dir / "q6_policies.png"
    plot_markdown(plot_path, md)
    add_figure(doc, plot_path, "Figure 1. Weeks at each price under the three markdown policies", width=5.7)
    add_answer_box(
        doc,
        "Answer",
        f"The new policy is to sell at $60 for {used[0][1]:.0f} weeks and then at $58 for {used[1][1]:.0f} weeks. Revenue rises by {fmt_money(rev_c - rev)} to {fmt_money(rev_c)}.",
    )
    add_text(
        doc,
        "Even with thirteen prices available, the optimal policy uses only two of them, and they are adjacent. This is a consequence of the extreme-point structure of the model: there are three constraints, the full-price constraint is slack, so at most two price levels can have positive weeks in a basic optimal solution. Because the inventory and the season both bind, the retailer wants an average selling rate of 2,000 / 15 = 133.3 units per week. On the coarse grid this rate is reached by mixing $60 (125 per week) and $54 (162.5 per week); the finer grid allows the closer pair $60 and $58 (137.5 per week), so fewer units have to be sold at a deep discount.",
    )
    add_text(
        doc,
        "The gain is real but modest, about 0.4% of revenue, even though the grid has more than three times as many price levels and asks for more price changes. Most of the value of markdown optimization is therefore already captured by a few well-chosen price levels, which supports the traditional practice when menu costs and customers' price perceptions matter.",
    )


def build_document(image_dir: Path) -> None:
    checks = verify_analytical_answers()
    diet = q5_diet.solve(with_fat=False)
    diet_fat = q5_diet.solve(with_fat=True)
    md = q6_markdown.solve()

    assert abs(diet["spend"] - diet_fat["spend"]) < 1e-9
    assert np.isclose(md["benchmark"][1], 116750) and np.isclose(md["b"]["revenue"], 114150)
    assert np.isclose(md["b"]["stick_revenue"], 113250) and np.isclose(md["c"][1], 117250)

    doc = new_document(2)
    add_question_1(doc, image_dir)
    add_question_2(doc, image_dir)
    add_question_3(doc, image_dir)
    add_question_4(doc, image_dir, checks)
    add_question_5(doc, image_dir, diet, diet_fat)
    add_question_6(doc, image_dir, md)

    doc.add_heading("Appendix: Computational Code", level=1)
    add_text(doc, "The following Gurobi code produced the numerical results reported for Questions 5 and 6.")
    doc.add_heading("Question 5: Diet problem", level=2)
    add_code_block(doc, (CODE_DIR / "q5_diet.py").read_text())
    doc.add_heading("Question 6: Markdown management", level=2)
    add_code_block(doc, (CODE_DIR / "q6_markdown.py").read_text())
    add_ai_declaration(doc)

    save_document(
        doc,
        OUTPUT_FILE,
        title="DBA5103 Assignment 2 Solutions",
        keywords="polyhedra, duality, complementary slackness, sensitivity analysis, diet problem, markdown",
    )


def main() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="dba5103_assignment2_"))
    try:
        build_document(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
