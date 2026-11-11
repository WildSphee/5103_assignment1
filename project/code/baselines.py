"""Feasible equal, largest-remainder proportional, and exact-marginal greedy rules."""
import heapq
import numpy as np
from scipy.sparse import coo_matrix
from model import make_solver, run, investments, allocate, summarise


def step_cost(inst, x, j):
    p = inst.p
    if x[j] + 1 > inst.maximum[j] or (x[j]+1)*p.ac_power > p.headroom + p.upgrade_kw + 1e-7:
        return np.inf
    before = x[j]*p.ac_power > p.headroom + 1e-7
    after = (x[j]+1)*p.ac_power > p.headroom + 1e-7
    return p.ac_cost + (p.fixed_cost if x[j] == 0 else 0) + (p.upgrade_cost if after and not before else 0)


def simple_rule(inst, budget, kind):
    x = np.zeros(inst.n, dtype=int)
    remaining = budget
    if kind == 'equal':
        while True:
            changed = False
            for j in range(inst.n):
                cost = step_cost(inst, x, j)
                if cost <= remaining + 1e-7:
                    x[j] += 1; remaining -= cost; changed = True
            if not changed:
                break
    elif kind == 'proportional':
        # Hamilton largest remainder for the nominal count; repair under actual step costs.
        w = inst.sites.lots.to_numpy() / inst.sites.lots.sum()
        nominal = int(budget // inst.p.ac_cost)
        ideal = nominal * w
        target = np.floor(ideal).astype(int)
        for j in np.lexsort((np.arange(inst.n), -(ideal-target)))[:nominal-target.sum()]:
            target[j] += 1
        for j in range(inst.n):
            for _ in range(target[j]):
                cost = step_cost(inst, x, j)
                if cost > remaining + 1e-7:
                    break
                x[j] += 1; remaining -= cost
        while True:
            candidates = [j for j in range(inst.n) if step_cost(inst, x, j) <= remaining + 1e-7]
            if not candidates:
                break
            j = min(candidates, key=lambda j: (-(ideal[j]-x[j]), j))
            remaining -= step_cost(inst, x, j); x[j] += 1
    else:
        raise ValueError(kind)
    flow, _ = allocate(inst, x)
    r = summarise(inst, x, np.zeros(inst.n), flow, budget, kind)
    r['algorithm'] = 'ID-ordered equal rounds' if kind == 'equal' else 'Hamilton largest remainder + feasible deficit repair'
    return r


def greedy_rule(inst, budget):
    """Lazy exact max-flow marginal per current step dollar, including upgrade thresholds.

    Max-flow served demand is submodular in added source capacities. Cached marginals
    are upper bounds as other site capacities grow. The selected site's step cost is
    recomputed after every addition, so an upgrade threshold cannot reuse an old price.
    Each tested marginal re-solves all allocations using a warm-started LP.
    """
    n, m, p = inst.n, len(inst.ii), inst.p
    A = coo_matrix((np.ones(2*m), (np.r_[inst.ii, n+inst.jj], np.tile(np.arange(m), 2))), shape=(2*n, m))
    h = make_solver(-np.ones(m), A, np.zeros(2*n), np.r_[inst.demand, inst.q0], np.zeros(m), np.full(m, np.inf), p=p)
    _, info = run(h, 'greedy_initial')
    service = -h.getObjectiveValue()
    x = np.zeros(n, dtype=int)
    remaining, generation, evaluations = budget, 0, 0
    heap = []
    for j in range(n):
        cost = step_cost(inst, x, j)
        if cost <= remaining:
            heapq.heappush(heap, (-p.q/cost, j, -1))
    trace = []
    while heap:
        negative_bound, j, age = heapq.heappop(heap)
        cost = step_cost(inst, x, j)
        if cost > remaining + 1e-7:
            continue
        oldcap = inst.q0[j] + p.q*x[j]
        h.changeRowBounds(n+j, 0, oldcap+p.q)
        _, info = run(h, 'greedy_marginal')
        assert info['status'] == 'Optimal'
        trial = -h.getObjectiveValue()
        gain = max(0., trial-service)
        ratio = gain/cost
        evaluations += 1
        if ratio + 1e-10 >= (-heap[0][0] if heap else 0):
            if gain <= 1e-6:
                h.changeRowBounds(n+j, 0, oldcap)
                break
            x[j] += 1; remaining -= cost; generation += 1; service = trial
            trace.append({'step': generation, 'site_id': inst.sites.car_park_no.iloc[j], 'step_capex': cost, 'marginal_kwh_day': gain, 'cumulative_capex': budget-remaining})
            newcost = step_cost(inst, x, j)
            if newcost <= remaining + 1e-7:
                heapq.heappush(heap, (-p.q/newcost, j, -1))
        else:
            h.changeRowBounds(n+j, 0, oldcap)
            _, back = run(h, 'greedy_restore')
            heapq.heappush(heap, (-ratio, j, generation))
    flow, _ = allocate(inst, x)
    assert abs(flow.sum()-service) < .02
    r = summarise(inst, x, np.zeros(n), flow, budget, 'greedy')
    r.update(marginal_lp_evaluations=evaluations, algorithm='Exact reassigned-flow marginal/step-cost greedy; lazy upper bounds')
    return r, trace
