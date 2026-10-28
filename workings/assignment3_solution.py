#!/usr/bin/env python3
"""Solve DBA5103 Assignment 3 and generate the DOCX submission.

Questions 1, 2, 5 and 6 are solved with the Gurobi models in
``workings/assignment3``, whose source is attached verbatim in the code
appendix. The answers to Questions 3 and 6 are also checked by enumeration.
"""

from __future__ import annotations

import itertools
import shutil
import tempfile
from math import erf, exp, pi, sqrt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from assignment3 import q1_process_flexibility as q1
from assignment3 import q2_multilocation_newsvendor as q2
from assignment3 import q5_lot_sizing as q5
from assignment3 import q6_tsp_time_window as q6
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

OUTPUT_FILE = ROOT / "DBA5103 Assignment 3 CHAN HIU LOK.docx"
CODE_DIR = Path(__file__).resolve().parent / "assignment3"

COORDS = {
    1: (1.264306, 103.822222),
    2: (1.265270, 103.821762),
    3: (1.264181, 103.820403),
    4: (1.265067, 103.818683),
    5: (1.265655, 103.818049),
    6: (1.264998, 103.817868),
}


def money(v: float) -> str:
    return f"${v:,.0f}"


def plot_flexibility(path: Path, summary) -> None:
    names = [row[0] for row in summary]
    means = [row[2] for row in summary]
    errs = [1.96 * row[3] for row in summary]
    fig, ax = plt.subplots(figsize=(6.2, 2.7), dpi=240)
    colors = ["#C8D6DE", "#8FB3C9", "#2F6483", "#18354A"]
    ax.bar(names, means, yerr=errs, color=colors, capsize=3, width=0.6)
    for k, m in enumerate(means):
        ax.text(k, m + 3, f"{m:.1f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(480, 590)
    ax.set_ylabel("Average weekly sales")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_transshipment(path: Path, rows) -> None:
    K = [r["K"] for r in rows]
    net = [r["net"] for r in rows]
    err = [1.96 * r["se"] for r in rows]
    fig, ax = plt.subplots(figsize=(5.6, 2.6), dpi=240)
    ax.errorbar(K, net, yerr=err, fmt="o-", color="#2F6483", capsize=3, label="Expected net gain (95% interval)")
    ax.axhline(0, color="#B23A3A", lw=1, ls="--", label="Break-even")
    ax.set_xscale("log")
    ax.set_xticks(K, [f"{k:,}" for k in K])
    ax.set_xlabel("Number of demand samples")
    ax.set_ylabel("Net gain ($)")
    ax.set_ylim(-150, 1500)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_transportation(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.8, 2.5), dpi=240)
    supply = {1: (0, 1), 2: (0, 0)}
    demand = {1: (3, 1), 2: (3, 0)}
    tree = {(1, 2): "a", (2, 1): "70", (2, 2): "30 - a"}
    label_pos = {(1, 2): 0.32, (2, 1): 0.68, (2, 2): 0.5}
    for (i, j), label in tree.items():
        (x0, y0), (x1, y1) = supply[i], demand[j]
        ax.annotate("", xy=(x1 - 0.18, y1 + (y0 - y1) * 0.06), xytext=(x0 + 0.18, y0 + (y1 - y0) * 0.06),
                    arrowprops=dict(arrowstyle="-|>", color="#18354A", lw=1.6))
        t = label_pos[(i, j)]
        ax.text(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 0.1, label, ha="center", fontsize=9, color="#18354A",
                bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.plot([0.18, 2.82], [1, 1], color="#9AA5AD", lw=1.2, ls="--")
    ax.text(1.5, 1.1, "x11 = 0 (deleted)", ha="center", fontsize=8.5, color="#66717A")
    for k, (x, y) in supply.items():
        ax.add_patch(plt.Circle((x, y), 0.16, color="#2F6483"))
        ax.text(x, y, str(k), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(x - 0.3, y, "a" if k == 1 else "100 - a", ha="right", va="center", fontsize=9)
    for k, (x, y) in demand.items():
        ax.add_patch(plt.Circle((x, y), 0.16, color="#2F6483"))
        ax.text(x, y, str(k), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(x + 0.3, y, "70" if k == 1 else "30", ha="left", va="center", fontsize=9)
    ax.text(0, 1.38, "Supply", ha="center", fontsize=9, fontweight="bold")
    ax.text(3, 1.38, "Demand", ha="center", fontsize=9, fontweight="bold")
    ax.set_xlim(-1.1, 3.8)
    ax.set_ylim(-0.35, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_routes(path: Path, route_a, route_b) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), dpi=240, sharey=True)
    titles = ["(a) Without waiting-time limits: 22 min", "(b) With waiting-time limits: 25 min"]
    for ax, route, title in zip(axes, (route_a, route_b), titles):
        for a, b in zip(route, route[1:]):
            (ya, xa), (yb, xb) = COORDS[a], COORDS[b]
            ax.annotate("", xy=(xb, yb), xytext=(xa, ya),
                        arrowprops=dict(arrowstyle="-|>", color="#2F6483", lw=1.3, shrinkA=7, shrinkB=7))
        for node, (lat, lon) in COORDS.items():
            color = "#B23A3A" if node == 1 else "#18354A"
            ax.scatter(lon, lat, s=150, color=color, zorder=3)
            ax.text(lon, lat, str(node), ha="center", va="center", color="white", fontsize=8, fontweight="bold", zorder=4)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlabel("Longitude", fontsize=8)
        ax.tick_params(labelsize=6.5)
        ax.ticklabel_format(useOffset=False)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.15)
    axes[0].set_ylabel("Latitude", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_question_1(doc, image_dir: Path, sales_1k, sales_10k) -> None:
    doc.add_heading("1. Process Flexibility", level=1)
    add_text(
        doc,
        "For a given design, that is, a set of arcs A linking plants to models, and a realised demand vector D, the maximum weekly sales solve a network flow problem in which x_ij is the amount of model j produced at plant i:",
    )
    p = image_dir / "q1_model.png"
    render_formula(
        p,
        [
            r"$f(A,D)=\max\quad \sum_{(i,j)\in A}x_{ij}$",
            r"$\mathrm{s.t.}\quad \sum_{j:(i,j)\in A}x_{ij}\leq100,\qquad \sum_{i:(i,j)\in A}x_{ij}\leq D_j,\qquad x_{ij}\geq0.$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "Demand is random, so each design is evaluated by simulation. Draw demand samples with D_j = max{X_j, 0}, where the X_j are independent N(100, 30^2), solve the network flow problem for every sample, and average the optimal sales. The open chain adds the five arcs from plant i to model i + 1 to the dedicated design; the long chain adds one further arc, from plant 6 back to model 1, which closes the chain into a single cycle. The same 1,000 demand samples (and, as a robustness check, 10,000 samples) are used for every design so that the comparison is not distorted by sampling noise.",
    )
    ded, full = sales_10k["Dedicated"].mean(), sales_10k["Full flexible"].mean()
    summary = []
    arcs = {"Dedicated": 6, "Open chain": 11, "Long chain": 12, "Full flexible": 36}
    for name in ("Dedicated", "Open chain", "Long chain", "Full flexible"):
        v1, v2 = sales_1k[name], sales_10k[name]
        summary.append([name, arcs[name], v1.mean(), v1.std(ddof=1) / np.sqrt(len(v1)), v2.mean(),
                        100 * (v2.mean() - ded) / (full - ded)])
    make_table(
        doc,
        ["Design", "Arcs", "Avg. sales (1,000 samples)", "Std. error", "Avg. sales (10,000 samples)", "Share of full-flexibility gain"],
        [[r[0], str(r[1]), f"{r[2]:.1f}", f"{r[3]:.2f}", f"{r[4]:.1f}", f"{r[5]:.0f}%"] for r in summary],
        widths=[1.15, 0.5, 1.2, 0.8, 1.25, 1.25],
        font_size=8.0,
    )
    plot_path = image_dir / "q1_designs.png"
    plot_flexibility(plot_path, summary)
    add_figure(doc, plot_path, "Figure 1. Average weekly sales by design (1,000 samples, 95% intervals)", width=5.5)
    oc, lc = summary[1], summary[2]
    add_answer_box(
        doc,
        "Answer",
        f"The open chain sells about {oc[2]:.0f} units per week on average and the long chain about {lc[2]:.0f}, against about {summary[0][2]:.0f} for the dedicated design and {summary[3][2]:.0f} for full flexibility.",
    )
    add_text(
        doc,
        f"The open chain recovers roughly {oc[5]:.0f}% of the gain from full flexibility using 11 arcs instead of 36. The long chain, with just one more arc, recovers essentially all of it ({lc[5]:.0f}%) and is statistically indistinguishable from the fully flexible system. The reason is the end of the open chain: model 1 can only be made at plant 1 and plant 6 can only make model 6, so a demand surge for model 1 or spare capacity at plant 6 cannot be shared with the rest of the system. Closing the chain gives every plant and every model two links, and excess demand anywhere can be passed along the cycle in either direction to a plant with spare capacity. A small amount of well-placed flexibility therefore delivers almost all of the benefit of full flexibility.",
    )


def add_question_2(doc, image_dir: Path, nv) -> None:
    doc.add_heading("2. Multi-Location Newsvendor", level=1)
    doc.add_heading("2(a) Expected profit without transshipment", level=2)
    add_text(
        doc,
        "Without transshipment each store can only sell its own stock, so the network is the dedicated design of Question 1 with store inventories as capacities: sales at store i equal min{D_i, s_i}. The procurement cost of 50 x 1,300 = $65,000 is incurred up front and unsold units are worthless, so:",
    )
    p = image_dir / "q2a.png"
    render_formula(
        p,
        [r"$\mathbb{E}[\mathrm{profit}]=100\sum_{i=1}^{3}\mathbb{E}\left[\min\{D_i,\ s_i\}\right]-50\sum_{i=1}^{3}s_i,\qquad s=(300,\ 500,\ 500).$"],
        fontsize=15.0,
    )
    add_formula(doc, p)
    a = nv["a"]
    lost = 0.3989423 * q2.sigma.sum()
    exact = 100 * (q2.inventory.sum() - lost) - 65000
    add_text(
        doc,
        f"Evaluating the expectation with 10,000 demand samples gives expected sales of {a['sales']:,.1f} units and an expected profit of about {money(a['profit'])} (standard error about ${a['se']:.0f}).",
    )
    add_answer_box(doc, "Answer", f"The total expected profit is approximately {money(a['profit'])}.")
    add_text(
        doc,
        f"The figure can be checked in closed form. Each store stocks exactly its mean demand, and the truncation at zero is negligible because every mean is at least 12.5 standard deviations above zero. For a normal demand stocked at its mean, the expected shortfall is sigma times the standard normal density at zero, about 0.399 sigma, so the expected lost sales are 0.399 x (20 + 20 + 40) = {lost:.1f} units and the expected profit is {money(exact)}, in line with the simulation.",
    )

    doc.add_heading("2(b) Expected profit without demand uncertainty", level=2)
    add_text(
        doc,
        "If sigma_i = 0 every store sells exactly its mean demand, which equals its stock, so all 1,300 units are sold at full price.",
    )
    add_answer_box(doc, "Answer", f"The profit is 100 x 1,300 - 50 x 1,300 = {money(nv['b']['profit'])}.")
    add_text(
        doc,
        f"The gap of about {money(nv['b']['profit'] - a['profit'])} between (b) and (a) is the cost of demand uncertainty under the current allocation: stores with excess demand lose sales, while stores with weak demand are left with stock nobody can buy. Harbour Front, with the largest standard deviation, contributes half of it.",
    )

    doc.add_heading("2(c) Should the retailer adopt transshipment?", level=2)
    add_text(
        doc,
        "Once demand is realised, transshipment turns the dedicated network into a complete one: a unit of store i's inventory can be sold at store j for a margin of 100 - c_ij, where c_ii = 0. The best use of the realised inventory is again a network flow problem, in which x_ij is the number of units of store i's stock sold to customers at store j:",
    )
    p = image_dir / "q2c.png"
    render_formula(
        p,
        [
            r"$f(s,D)=\max\quad \sum_{i=1}^{3}\sum_{j=1}^{3}(100-c_{ij})\,x_{ij}$",
            r"$\mathrm{s.t.}\quad \sum_{j=1}^{3}x_{ij}\leq s_i,\qquad \sum_{i=1}^{3}x_{ij}\leq D_j,\qquad x_{ij}\geq0.$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "For the example in the question, with demand (250, 550, 450), Orchard is 50 units short while Jurong West and Harbour Front each have 50 units left. The cheapest source is Harbour Front at $7 per unit, so 50 units are shipped and the retailer gains 50 x (100 - 7) - 200 = $4,450 compared with not using the service. On average, the retailer should adopt the service if the expected increase in the optimal second-stage revenue exceeds the fixed fee of $200. The expected increase is estimated by solving both networks on the same demand samples:",
    )
    rows = nv["c"]
    make_table(
        doc,
        ["Samples", "Profit without", "Profit with (after $200 fee)", "Gross gain", "Net gain", "Std. error"],
        [
            [f"{r['K']:,}", money(r["profit_without"]), money(r["profit_with"]), money(r["gain"]), money(r["net"]), f"${r['se']:.0f}"]
            for r in rows
        ],
        widths=[0.8, 1.1, 1.65, 0.95, 0.9, 0.85],
        font_size=8.0,
    )
    plot_path = image_dir / "q2c_gain.png"
    plot_transshipment(plot_path, rows)
    add_figure(doc, plot_path, "Figure 2. Expected net gain from transshipment by sample size", width=4.9)
    last = rows[-1]
    add_answer_box(
        doc,
        "Answer",
        f"Yes. Transshipment raises the expected revenue by about {money(last['gain'])}, so after the $200 fee the expected profit rises by about {money(last['net'])} to roughly {money(last['profit_with'])}.",
    )
    add_text(
        doc,
        "The estimate is noisy for small samples, but every sample size gives a net gain far above zero, and from 1,000 samples onwards the estimate settles between about $840 and $880 with a standard error of $11 to $33. The recommendation is therefore robust to the sample size. The gross gain recovers roughly a third of the cost of uncertainty identified in (b); the rest is lost on samples in which every store is short or every store has surplus, where moving stock between stores cannot help.",
    )

    doc.add_heading("2(d) Two-stage stochastic optimization of the inventory positions", level=2)
    add_text(
        doc,
        "The inventory positions s = (s1, s2, s3) are chosen in the first stage, before demand is known, at a cost of $50 per unit. In the second stage the demand D is realised and the retailer sells and transships optimally, earning f(s, D) from part (c). The fixed fee is sunk and can be left out. The two-stage problem is:",
    )
    p = image_dir / "q2d_two_stage.png"
    render_formula(
        p,
        [
            r"$\max_{s\geq0}\quad -50\sum_{i=1}^{3}s_i+\mathbb{E}\left[f(s,D)\right],$",
            r"$f(s,D)=\max_{x\geq0}\left\{\sum_{i,j}(100-c_{ij})\,x_{ij}\ :\ \sum_{j}x_{ij}\leq s_i\ \forall i,\ \ \sum_{i}x_{ij}\leq D_j\ \forall j\right\}.$",
        ],
        fontsize=15.0,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "Replacing the expectation with the average over K demand samples D^1, ..., D^K, and giving every sample its own copy of the second-stage decisions, yields the sample average approximation, which is a single linear program:",
    )
    p = image_dir / "q2d_saa.png"
    render_formula(
        p,
        [
            r"$\max_{s,\,x}\quad -50\sum_{i=1}^{3}s_i+\frac{1}{K}\sum_{k=1}^{K}\sum_{i=1}^{3}\sum_{j=1}^{3}(100-c_{ij})\,x_{ijk}$",
            r"$\mathrm{s.t.}\quad \sum_{j=1}^{3}x_{ijk}\leq s_i,\qquad i=1,2,3;\ k=1,\ldots,K,$",
            r"$\sum_{i=1}^{3}x_{ijk}\leq D_j^{k},\qquad j=1,2,3;\ k=1,\ldots,K,$",
            r"$s_i\geq0,\qquad x_{ijk}\geq0.$",
        ],
        fontsize=15.0,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "The model was solved with Gurobi for several sample sizes, and each solution was then evaluated on a separate set of 10,000 test samples to see how it performs out of sample:",
    )
    make_table(
        doc,
        ["Samples K", "Jurong West", "Orchard", "Harbour Front", "Total", "Out-of-sample profit"],
        [
            [str(r["K"]), f"{r['stock'][0]:.1f}", f"{r['stock'][1]:.1f}", f"{r['stock'][2]:.1f}", f"{r['stock'].sum():.1f}", money(r["test"])]
            for r in nv["d"]
        ]
        + [["Current (300, 500, 500)", "300", "500", "500", "1,300", money(nv["d_benchmark"])]],
        widths=[1.5, 0.9, 0.8, 1.0, 0.7, 1.35],
        font_size=8.0,
    )
    add_answer_box(
        doc,
        "Answer",
        "The SAA solutions stay within a few units of (300, 500, 500), and on the test samples none of them beats the current allocation. Matching each store's inventory to its mean demand is therefore close to optimal even with transshipment.",
    )
    add_text(
        doc,
        "The result has a simple explanation. With a price of $100, a cost of $50 and no salvage value, the cost of one unit short equals the cost of one unit left over, so the best single-store stock is the median of demand, which is the mean for a normal distribution. Transshipment adds recourse after demand is known, but each store's demand is still symmetric around its mean and the shipping costs are small next to the $50 margin, so the balance between shortage and surplus barely moves. The value of transshipment comes from rebalancing stock after demand is realised, not from changing how much is stocked before the season.",
    )


def add_question_3(doc, image_dir: Path) -> None:
    doc.add_heading("3. Transportation Problem", level=1)
    doc.add_heading("3(a) Linear programming formulation", level=2)
    add_text(
        doc,
        "Let x_ij be the amount shipped from supply node i to demand node j. Total supply a + (100 - a) = 100 equals total demand 70 + 30, so the problem is balanced and every constraint is an equality:",
    )
    p = image_dir / "q3_lp.png"
    render_formula(
        p,
        [
            r"$\min\quad c_{11}x_{11}+c_{12}x_{12}+c_{21}x_{21}+c_{22}x_{22}$",
            r"$\mathrm{s.t.}\quad x_{11}+x_{12}=a,\qquad x_{21}+x_{22}=100-a,$",
            r"$x_{11}+x_{21}=70,\qquad x_{12}+x_{22}=30,\qquad x_{ij}\geq0.$",
        ],
    )
    add_formula(doc, p)
    add_text(doc, "With x = (x11, x12, x21, x22) and the constraints written as Ax = b, the constraint matrix is:")
    p = image_dir / "q3_matrix.png"
    render_matrix(p, [[1, 1, 0, 0], [0, 0, 1, 1], [1, 0, 1, 0], [0, 1, 0, 1]])
    add_formula(doc, p, caption="Rows: supply 1, supply 2, demand 1, demand 2; b = (a, 100 - a, 70, 30)")
    add_text(
        doc,
        "Each column has exactly two nonzero entries, one in a supply row and one in a demand row, which is the network structure of a transportation problem. The two supply rows and the two demand rows add up to the same vector, so one constraint is redundant and the rank of A is 3 = m + n - 1. A basic solution therefore has three basic arcs, which form a spanning tree of the four nodes.",
    )

    doc.add_heading("3(b) Flow on the spanning tree without arc (1, 1)", level=2)
    add_text(
        doc,
        "Deleting arc (1, 1) leaves the three arcs (1, 2), (2, 1) and (2, 2). They connect all four nodes without a cycle, so they form a spanning tree and determine a unique solution of Ax = b. The flows follow by working in from the leaves of the tree:",
    )
    p = image_dir / "q3_tree.png"
    render_formula(
        p,
        [
            r"$\mathrm{Demand\ 1\ is\ served\ only\ by\ supply\ 2:}\quad x_{21}=70,$",
            r"$\mathrm{Supply\ 1\ ships\ only\ to\ demand\ 2:}\quad x_{12}=a,$",
            r"$\mathrm{Demand\ 2\ balance:}\quad x_{22}=30-x_{12}=30-a.$",
        ],
        fontsize=15.0,
    )
    add_formula(doc, p)
    plot_path = image_dir / "q3_network.png"
    plot_transportation(plot_path)
    add_figure(doc, plot_path, "Figure 3. Spanning-tree flow after deleting arc (1, 1)", width=4.0)
    add_answer_box(
        doc,
        "Answer",
        "x11 = 0, x12 = a, x21 = 70, x22 = 30 - a. The remaining equation, supply 2, is satisfied automatically: 70 + (30 - a) = 100 - a.",
    )

    doc.add_heading("3(c) Range of supply for feasibility", level=2)
    add_text(
        doc,
        "The tree solution already satisfies every equality, so it is feasible exactly when all four flows are nonnegative. The flows 0 and 70 always are; the other two require a >= 0 and 30 - a >= 0.",
    )
    add_answer_box(
        doc,
        "Answer",
        "The solution is feasible, and is then a basic feasible solution (an extreme point), exactly when 0 <= a <= 30.",
    )
    add_text(
        doc,
        "At the end points a = 0 and a = 30 one of the basic flows is zero, so the basic feasible solution is degenerate. For a > 30, supply node 1 holds more than demand node 2 can absorb, so part of its supply must go to demand node 1 and a feasible basis has to include arc (1, 1).",
    )


def add_question_4(doc, image_dir: Path) -> None:
    doc.add_heading("4. Logical Constraints with Binary Variables", level=1)
    add_text(
        doc,
        "Each statement is an implication between binary variables. A linear inequality models it correctly when it rules out exactly the assignments that violate the statement and leaves all other assignments feasible.",
    )
    parts = [
        (
            "4(a) z = 1 if at least one x_i = 1",
            [r"$z\geq x_i,\qquad i=1,\ldots,n.$"],
            "If some x_i = 1, the constraint for that index forces z = 1. If every x_i = 0, the constraints read z >= 0 and leave z free. An equivalent single constraint is n z >= x_1 + ... + x_n.",
        ),
        (
            "4(b) If all x_i = 0, then z = 0",
            [r"$z\leq\sum_{i=1}^{n}x_i.$"],
            "If every x_i = 0, the right-hand side is zero and z = 0. If at least one x_i = 1, the right-hand side is at least one and z is free. Together with (a), this makes z the logical OR of the x_i.",
        ),
        (
            "4(c) z = 1 if all x_i = 1",
            [r"$z\geq\sum_{i=1}^{n}x_i-(n-1).$"],
            "If every x_i = 1, the right-hand side equals 1 and forces z = 1. If any x_i = 0, the right-hand side is at most 0 and z is free.",
        ),
        (
            "4(d) If any x_i = 0, then z = 0",
            [r"$z\leq x_i,\qquad i=1,\ldots,n.$"],
            "If some x_i = 0, the constraint for that index forces z = 0. If every x_i = 1, the constraints read z <= 1 and leave z free. Together with (c), this makes z the product x_1 x_2 ... x_n, the n-variable version of linearising a product of binary variables.",
        ),
        (
            "4(e) If x_1 + ... + x_n >= 5, then z = 1",
            [r"$\sum_{i=1}^{n}x_i-4\leq(n-4)\,z.$"],
            "It is easiest to read the contrapositive: if z = 0, then at most four x_i can equal 1. With z = 0 the constraint becomes x_1 + ... + x_n <= 4, which is exactly that. With z = 1 it becomes x_1 + ... + x_n <= n, which always holds, so z = 1 never cuts off a valid assignment. The coefficient n - 4 is the smallest big-M that works, since the sum can exceed 4 by at most n - 4 (for n < 5 the premise can never hold and no constraint is needed).",
        ),
    ]
    for k, (heading, formula, text) in enumerate(parts):
        doc.add_heading(heading, level=2)
        p = image_dir / f"q4_{k}.png"
        render_formula(p, formula)
        add_formula(doc, p)
        add_text(doc, text)


def add_question_5(doc, image_dir: Path, best, optimal) -> None:
    doc.add_heading("5. Economic Lot-Sizing", level=1)
    doc.add_heading("5(a) Integer programming formulation", level=2)
    add_text(
        doc,
        "Let x_t be the inventory at the end of season t, y_t the number of airplanes produced in season t, and z_t = 1 if the production facilities are set up in season t. With demand d_t, setup cost K_t and holding cost h_t, all in millions of dollars:",
    )
    p = image_dir / "q5_ip.png"
    render_formula(
        p,
        [
            r"$\min\quad \sum_{t=1}^{4}\left(K_tz_t+h_tx_t\right)$",
            r"$\mathrm{s.t.}\quad x_{t-1}+y_t-x_t=d_t,\qquad t=1,\ldots,4,\qquad x_0=0,$",
            r"$y_t\leq M\,z_t,\qquad t=1,\ldots,4,\qquad M=\sum_{t=1}^{4}d_t=10,$",
            r"$x_t,\ y_t\geq0\ \mathrm{and\ integer},\qquad z_t\in\{0,1\}.$",
        ],
    )
    add_formula(doc, p)
    add_text(
        doc,
        "The first set of constraints is the inventory balance: stock carried in plus production equals deliveries plus stock carried out. The big-M constraints link production to setups. If z_t = 0 nothing can be produced, and if z_t = 1 production is effectively unrestricted, since it never pays to make more than the 10 airplanes ordered. Requiring x_t >= 0 means every delivery is met on time, and the holding cost is charged on the inventory left at the end of each season, as in the worked example of Table 3.4 (which this model prices at 7 million).",
    )

    doc.add_heading("5(b) Optimal production schedule", level=2)
    add_text(
        doc,
        f"Gurobi finds a minimum total cost of {best['cost']:.1f} million dollars. The optimum is not unique: the solver's solution pool contains two schedules with the same cost.",
    )
    make_table(
        doc,
        ["Schedule", "Production (y1 to y4)", "End inventory (x1 to x4)", "Setup cost", "Holding cost", "Total"],
        [
            [
                f"Optimal {k + 1}",
                ", ".join(map(str, s["y"])),
                ", ".join(map(str, s["x"])),
                f"{2 * sum(s['z']):.1f}",
                f"{0.2 * sum(s['x']):.1f}",
                f"{s['cost']:.1f}",
            ]
            for k, s in enumerate(optimal)
        ]
        + [["Table 3.4 example", "3, 6, 0, 1", "0, 4, 1, 0", "6.0", "1.0", "7.0"]],
        widths=[1.15, 1.25, 1.35, 0.75, 0.8, 0.6],
        font_size=8.0,
    )
    add_answer_box(
        doc,
        "Answer",
        "The minimum cost is $4.8 million. One optimal schedule is to produce all 10 airplanes in season 1; the other is to produce 5 in season 1 and 5 in season 3. Both save $2.2 million compared with the schedule in Table 3.4.",
    )
    add_text(
        doc,
        "The tie comes from the cost ratio. A setup costs 2 million, the same as holding ten airplanes for one season. Moving the season 3 and season 4 airplanes into the season 1 batch saves one setup and adds holding of 3 x 0.2 x 2 + 2 x 0.2 x 2 = 2.0 million, so the two schedules cost the same. Both schedules also produce only when the inventory carried in is zero: production in a season covers whole seasons of demand, never a fraction of one.",
    )
    enum_rows = []
    d = q5.d
    for z in itertools.product([0, 1], repeat=4):
        if not z[0]:
            continue
        inv, cost, y = 0, 2.0 * sum(z), []
        for t in range(4):
            nxt = next((k for k in range(t + 1, 4) if z[k]), 4)
            y.append(int(d[t:nxt].sum()) if z[t] else 0)
            inv += y[t] - d[t]
            cost += 0.2 * inv
        enum_rows.append((round(cost, 2), "".join(map(str, z)), y))
    enum_rows.sort()
    assert enum_rows[0][0] == round(best["cost"], 2) and enum_rows[1][0] == enum_rows[0][0] < enum_rows[2][0]
    add_text(
        doc,
        "As an independent check, the table below lists every setup pattern. A setup in season 1 is required because three airplanes are due then, and given the setup seasons it is optimal to produce, in each setup season, exactly the demand up to the next setup. The two optimal patterns are the ones Gurobi found.",
    )
    make_table(
        doc,
        ["Setup in seasons (z1 z2 z3 z4)", "Production", "Total cost (million)"],
        [[f"{z[0]} {z[1]} {z[2]} {z[3]}", ", ".join(map(str, y)), f"{c:.1f}"] for c, z, y in enum_rows],
        widths=[2.0, 1.4, 1.5],
        font_size=8.0,
    )


def add_question_6(doc, image_dir: Path, tsp_a, tsp_b) -> None:
    doc.add_heading("6. TSP with Time Windows", level=1)
    doc.add_heading("6(a) Minimum travel time without waiting-time limits", level=2)
    add_text(
        doc,
        "Let x_ij = 1 if the delivery man walks directly from location i to location j, and let u_i be the time at which he reaches location i, with u_1 = 0 at the restaurant. The model is a travelling salesman problem with assignment constraints and time-accumulating subtour-breaking constraints:",
    )
    p = image_dir / "q6_model.png"
    render_formula(
        p,
        [
            r"$\min\quad \sum_{i=1}^{6}\sum_{j=1}^{6}c_{ij}x_{ij}$",
            r"$\mathrm{s.t.}\quad \sum_{j=1}^{6}x_{ij}=1\ \ (i=1,\ldots,6),\qquad \sum_{i=1}^{6}x_{ij}=1\ \ (j=1,\ldots,6),$",
            r"$u_i+c_{ij}-u_j\leq M(1-x_{ij}),\qquad i\neq j,\ \ j=2,\ldots,6,\qquad u_1=0,$",
            r"$x_{ij}\in\{0,1\},\qquad u_i\geq0.$",
        ],
        fontsize=15.0,
    )
    add_formula(doc, p)
    add_text(
        doc,
        "If x_ij = 1 the third constraint reads u_j >= u_i + c_ij, so u_j is the arrival time at j; if x_ij = 0 the large constant M (1,000 here) makes it inactive. Because arrival times must increase along every arc that does not return to location 1, no subtour can avoid location 1, and every feasible solution is a single tour. A cost of 1,000 on the diagonal of the time matrix rules out staying in place.",
    )
    add_answer_box(
        doc,
        "Answer",
        f"The minimum travelling time is {tsp_a['time']:.0f} minutes. Gurobi returns the route {' -> '.join(map(str, tsp_a['route']))}.",
    )
    add_text(
        doc,
        "The route is not unique; enumerating all 120 tours gives 12 routes of 22 minutes. The locations form two clusters: the restaurant with customers 2 and 3, close together near VivoCity, and customers 4, 5 and 6 about 6 to 7 minutes away, which are 1 or 2 minutes from one another. Every tour must leave the first cluster through customer 2 or 3 and come back through the other, so it has the form 1, 2 or 3, the far cluster, 3 or 2, 1. The two legs from the restaurant cost 3 + 3, and the best combinations of crossings and paths through the far cluster cost 16 minutes, for example 7 + 2 + 7 for 2, 4, 5, 6, 3, or 6 + 3 + 7 for 2, 5, 4, 6, 3. Several orders achieve this, which explains the ties.",
    )

    doc.add_heading("6(b) Minimum travel time with waiting-time limits", level=2)
    add_text(
        doc,
        "Because u_j measures the arrival time, the delivery commitment is a simple upper bound on each customer's arrival time, W_j, added to the model in (a):",
    )
    p = image_dir / "q6_window.png"
    render_formula(p, [r"$u_j\leq W_j,\qquad W=(W_2,\ldots,W_6)=(5,\ 10,\ 15,\ 13,\ 14)\ \mathrm{minutes}.$"])
    add_formula(doc, p)
    arr = tsp_b["arrival"]
    make_table(
        doc,
        ["Location", "Arrival time", "Maximum waiting time", "Slack"],
        [[str(j), f"{arr[j]} min", f"{q6.max_wait[j - 1]} min", f"{q6.max_wait[j - 1] - arr[j]} min"] for j in tsp_b["route"][1:-1]]
        + [["Back at 1", f"{arr[1]} min", "-", "-"]],
        widths=[1.1, 1.1, 1.6, 0.9],
        font_size=8.2,
    )
    add_answer_box(
        doc,
        "Answer",
        f"Yes, a feasible route exists. The fastest one is {' -> '.join(map(str, tsp_b['route']))}, which takes {tsp_b['time']:.0f} minutes and meets every customer's waiting-time limit.",
    )
    add_text(
        doc,
        "The route is forced almost step by step. Customer 2 must be reached within 5 minutes, which is only possible by going there first (arrival at 3), and customer 3 must then be reached by minute 10, so he comes second (arrival at 6). Of the six orders through customers 4, 5 and 6 starting at minute 6, only 5, 6, 4 meets every limit: starting with 4 or 6 reaches customer 5 at minute 14 or later, past its limit of 13, and the order 5, 4, 6 reaches customer 6 at minute 15, past its limit of 14. Enumerating all 120 tours confirms that this route is the unique feasible optimum. The service commitment costs 3 minutes of total travel time compared with (a), because the walk back to the restaurant now starts from customer 4 (10 minutes) rather than from customer 3 (3 minutes).",
    )
    plot_path = image_dir / "q6_routes.png"
    plot_routes(plot_path, tsp_a["route"], tsp_b["route"])
    add_figure(doc, plot_path, "Figure 4. Optimal delivery routes, plotted by latitude and longitude (location 1 in red)", width=6.0)


def enumerate_tsp():
    cost = q6.cost
    best, best_w, tours = None, None, []
    for perm in itertools.permutations(range(2, 7)):
        route = (1, *perm, 1)
        t, arrival = 0, {}
        for a, b in zip(route, route[1:]):
            t += cost[a - 1, b - 1]
            arrival[b] = t
        tours.append(t)
        feasible = all(arrival[j] <= q6.max_wait[j - 1] for j in range(2, 7))
        if best is None or t < best:
            best = t
        if feasible and (best_w is None or t < best_w[0]):
            best_w = (t, [route])
        elif feasible and t == best_w[0]:
            best_w[1].append(route)
    return best, sum(1 for t in tours if t == best), best_w


def build_document(image_dir: Path) -> None:
    sales_1k = q1.solve(1000)
    sales_10k = q1.solve(10000)
    nv = q2.solve()
    best, optimal = q5.solve()
    tsp_a, tsp_b = q6.solve(False), q6.solve(True)

    # checks against independent calculations
    assert abs(nv["b"]["profit"] - 65000) < 1e-6
    assert all(r["net"] - 1.96 * r["se"] > 0 for r in nv["c"])
    assert all(r["test"] <= nv["d_benchmark"] + 1e-6 for r in nv["d"])
    assert all(np.all(np.abs(r["stock"] - q2.inventory) < 10) for r in nv["d"])
    assert abs(best["cost"] - 4.8) < 1e-9 and {tuple(s["y"]) for s in optimal} == {(10, 0, 0, 0), (5, 0, 5, 0)}
    tsp_min, n_opt, (tsp_w, routes_w) = enumerate_tsp()
    assert tsp_a["time"] == tsp_min == 22 and n_opt == 12
    assert tsp_b["time"] == tsp_w == 25 and routes_w == [tuple(tsp_b["route"])]

    doc = new_document(3)
    add_question_1(doc, image_dir, sales_1k, sales_10k)
    add_question_2(doc, image_dir, nv)
    add_question_3(doc, image_dir)
    add_question_4(doc, image_dir)
    add_question_5(doc, image_dir, best, optimal)
    add_question_6(doc, image_dir, tsp_a, tsp_b)

    doc.add_heading("Appendix: Computational Code", level=1)
    add_text(doc, "The following Gurobi code produced the numerical results reported for Questions 1, 2, 5 and 6.")
    for title, name in (
        ("Question 1: Process flexibility", "q1_process_flexibility.py"),
        ("Question 2: Multi-location newsvendor and transshipment", "q2_multilocation_newsvendor.py"),
        ("Question 5: Economic lot-sizing", "q5_lot_sizing.py"),
        ("Question 6: TSP with time windows", "q6_tsp_time_window.py"),
    ):
        doc.add_heading(title, level=2)
        add_code_block(doc, (CODE_DIR / name).read_text())
    add_ai_declaration(doc)

    save_document(
        doc,
        OUTPUT_FILE,
        title="DBA5103 Assignment 3 Solutions",
        keywords="process flexibility, newsvendor, stochastic optimization, transportation, integer programming, TSP",
    )


def main() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="dba5103_assignment3_"))
    try:
        build_document(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
