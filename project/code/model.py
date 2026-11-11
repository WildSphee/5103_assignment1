"""Capacitated location MILP and fixed-investment transportation LP (HiGHS)."""
from dataclasses import dataclass, replace, asdict
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import highspy as hs
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
from prepare_data import INPUTS, OUT


@dataclass(frozen=True)
class Parameters:
    stock: float = 117116.83333333333
    hdb_share: float = .4
    dependence: float = .8
    annual_km: float = 16200
    intensity: float = .16
    efficiency: float = .9
    hours: float = 6
    availability: float = .97
    power_factor: float = .85
    radius: float = 400
    path_inflation: float = 1
    ac_power: float = 7.4
    dc_power: float = 50
    dc_hours: float = 6
    dc_power_factor: float = .85
    ac_cost: float = 6500
    dc_cost: float = 60000
    fixed_cost: float = 0
    upgrade_cost: float = 50000
    ac_maintenance: float = 380
    dc_maintenance: float = 1180
    network: float = 200
    lifetime: float = 10
    discount: float = .05
    headroom: float = 44.4
    upgrade_kw: float = 88.8
    lot_share: float = .1
    impute_factor: float = 1
    unknown_no_build: bool = False
    weights: str = 'lots'
    matching: str = 'strict'
    power_bound: str = 'lower'
    deduplicate_bays: bool = False
    dc_enabled: bool = False
    seed: int = 17
    time_limit: float = 45
    mip_gap: float = .0001

    @property
    def q(self):
        return self.ac_power * self.hours * self.availability * self.power_factor

    @property
    def qdc(self):
        return self.dc_power * self.dc_hours * self.availability * self.dc_power_factor

    @property
    def crf(self):
        return self.discount / (1 - (1 + self.discount) ** -self.lifetime) if self.discount else 1 / self.lifetime


@dataclass
class Instance:
    sites: pd.DataFrame
    p: Parameters
    demand: np.ndarray
    q0: np.ndarray
    bays: np.ndarray
    maximum: np.ndarray
    ii: np.ndarray
    jj: np.ndarray
    distances: np.ndarray
    unallocated_proxy_share: float = 0

    @property
    def n(self):
        return len(self.demand)


def build_instance(p=None):
    p = p or Parameters()
    s = pd.read_csv(INPUTS / 'sites.csv')
    supply = pd.read_csv(INPUTS / 'existing_supply.csv')
    assert s.car_park_no.tolist() == supply.site_id.tolist()
    lots = s.lots.to_numpy().copy()
    lots[s.imputed] *= p.impute_factor
    weights = lots / lots.sum()
    missing_share = 0.
    if p.weights != 'lots':
        a = pd.read_csv(INPUTS / 'area_demand_weights.csv')
        year = 2026 if p.weights.endswith('2026') else 2025
        metric = 'population' if p.weights.startswith('population') else 'dwellings'
        a = a[(a.year == year) & (a.metric == metric)].set_index('area').value
        area = s['area_2025' if year == 2026 else 'area_2019']
        area_lots = pd.Series(lots).groupby(area).sum()
        missing_share = float(a.loc[~a.index.isin(area_lots.index)].sum() / a.sum())
        # Preserve the national HDB total and disclose any no-site area proxy reallocation.
        available = a.reindex(area_lots.index).fillna(0)
        weights = (area.map(available / available.sum()).to_numpy() * lots / area.map(area_lots).to_numpy())
    per_ev = p.dependence * p.annual_km / 365 * p.intensity / p.efficiency
    demand = p.stock * p.hdb_share * per_ev * weights
    q0 = supply[f'{p.matching}_kw_{p.power_bound}'].to_numpy() * p.hours * p.availability * p.power_factor
    # Existing DC retains its recorded rated power under the same declared effective-hours base.
    bays = supply[f'{p.matching}_points'].to_numpy()
    if p.deduplicate_bays and p.matching == 'strict':
        bays = supply.strict_bays_deduplicated.to_numpy()
    maximum = np.maximum(0, np.floor(p.lot_share * lots) - bays).astype(int)
    if p.unknown_no_build:
        maximum[s.imputed] = 0
    coords = s[['x_coord', 'y_coord']].to_numpy()
    tree = cKDTree(coords)
    arcs = [(i, j) for i, hits in enumerate(tree.query_ball_tree(tree, p.radius / p.path_inflation)) for j in sorted(hits)]
    ii, jj = np.array(arcs, dtype=int).T
    dist = np.linalg.norm(coords[ii] - coords[jj], axis=1) * p.path_inflation
    assert np.isclose(weights.sum(), 1) and np.all(demand >= 0)
    return Instance(s, p, demand, q0, bays, maximum, ii, jj, dist, missing_share)


def make_solver(c, A, lower, upper, lb, ub, integer=None, p=None, log=None):
    p = p or Parameters()
    A = A.tocsc()
    lp = hs.HighsLp()
    lp.num_col_, lp.num_row_ = len(c), len(lower)
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = c, lb, ub
    lp.row_lower_, lp.row_upper_ = lower, upper
    lp.a_matrix_.format_ = hs.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = A.indptr, A.indices, A.data
    if integer is not None:
        lp.integrality_ = [hs.HighsVarType.kInteger if t else hs.HighsVarType.kContinuous for t in integer]
    h = hs.Highs()
    h.setOptionValue('output_flag', bool(log))
    h.setOptionValue('log_to_console', False)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        h.setOptionValue('log_file', str(log))
    h.setOptionValue('threads', 1)
    h.setOptionValue('random_seed', p.seed)
    h.setOptionValue('time_limit', p.time_limit)
    h._per_solve_seconds = p.time_limit
    h.setOptionValue('mip_rel_gap', p.mip_gap)
    h.setOptionValue('mip_feasibility_tolerance', 1e-7)
    h.setOptionValue('primal_feasibility_tolerance', 1e-7)
    assert h.passModel(lp) == hs.HighsStatus.kOk
    return h


def solve_info(h, stage, elapsed):
    info = h.getInfo()
    return {'stage': stage, 'status': h.modelStatusToString(h.getModelStatus()),
            'objective': h.getObjectiveValue(), 'bound': info.mip_dual_bound,
            'gap': info.mip_gap, 'nodes': info.mip_node_count, 'seconds': elapsed,
            'max_primal_infeasibility': info.max_primal_infeasibility}


def run(h, stage):
    # HiGHS run time accumulates when one solver is reused. Give each new solve
    # its own limit, especially for the thousands of warm-started greedy LPs.
    h.setOptionValue('time_limit', h.getRunTime() + h._per_solve_seconds)
    start = time.perf_counter()
    h.run()
    info = solve_info(h, stage, time.perf_counter() - start)
    if not h.getSolution().value_valid:
        return None, info
    return np.array(h.getSolution().col_value), info


def investments(inst, x, d=None):
    p = inst.p
    d = np.zeros(inst.n) if d is None else d
    z = (x + d > 0).astype(int)
    y = (p.ac_power * x + p.dc_power * d > p.headroom + 1e-7).astype(int)
    capital = p.ac_cost * x + p.dc_cost * d + p.fixed_cost * z + p.upgrade_cost * y
    annual = p.crf * capital + (p.ac_maintenance + p.network) * x + (p.dc_maintenance + p.network) * d
    return z, y, capital, annual


def allocate(inst, x=None, d=None, distance=True, q_override=None):
    """Max-flow LP, followed by min-distance flow with service preserved."""
    n, m = inst.n, len(inst.ii)
    x = np.zeros(n) if x is None else np.array(x)
    d = np.zeros(n) if d is None else np.array(d)
    q = inst.q0 + inst.p.q * x + inst.p.qdc * d if q_override is None else q_override
    rows = np.r_[inst.ii, n + inst.jj]
    cols = np.tile(np.arange(m), 2)
    A = coo_matrix((np.ones(2*m), (rows, cols)), shape=(2*n, m))
    h = make_solver(-np.ones(m), A, np.zeros(2*n), np.r_[inst.demand, q], np.zeros(m), np.full(m, np.inf), p=inst.p)
    sol, info = run(h, 'allocation_max_service')
    if sol is None:
        raise RuntimeError(info)
    served = sol.sum()
    if distance and served > 0:
        epsilon = max(1e-6, 1e-8 * inst.demand.sum())
        h.addRow(served - epsilon, np.inf, m, np.arange(m, dtype=np.int32), np.ones(m))
        h.changeColsCost(m, np.arange(m, dtype=np.int32), inst.distances / 1000)
        candidate, dist_info = run(h, 'allocation_min_distance')
        if candidate is not None:
            sol = candidate
    return sol, info


def formulation(inst, budget=np.inf, target=None, relaxation=False):
    """Column blocks f, x_AC, x_DC, z, y; unmet demand eliminated as D - sum(f)."""
    p, n, m = inst.p, inst.n, len(inst.ii)
    nv = m + 4*n
    ix, idc, iz, iy = [m + k*n + np.arange(n) for k in range(4)]
    rr, cc, vv, lower, upper = [], [], [], [], []

    def row(cols, vals, lo=-np.inf, hi=np.inf):
        k = len(lower)
        rr.extend([k]*len(cols)); cc.extend(cols); vv.extend(vals)
        lower.append(lo); upper.append(hi)

    by_i = [[] for _ in range(n)]; by_j = [[] for _ in range(n)]
    for a, (i, j) in enumerate(zip(inst.ii, inst.jj)):
        by_i[i].append(a); by_j[j].append(a)
    for i in range(n):
        row(by_i[i], [1]*len(by_i[i]), hi=inst.demand[i])
    for j in range(n):
        row(by_j[j] + [ix[j], idc[j]], [1]*len(by_j[j]) + [-p.q, -p.qdc], hi=inst.q0[j])
        row([ix[j], idc[j], iz[j]], [1, 1, -inst.maximum[j]], hi=0)
        row([iz[j], ix[j], idc[j]], [1, -1, -1], hi=0)
        row([ix[j], idc[j], iy[j]], [p.ac_power, p.dc_power, -p.upgrade_kw], hi=p.headroom)
        row([iy[j], iz[j]], [1, -1], hi=0)
    cap = np.r_[np.zeros(m), np.full(n, p.ac_cost), np.full(n, p.dc_cost), np.full(n, p.fixed_cost), np.full(n, p.upgrade_cost)]
    ann = p.crf * cap
    ann[ix] += p.ac_maintenance + p.network
    ann[idc] += p.dc_maintenance + p.network
    if np.isfinite(budget):
        row(list(range(m, nv)), cap[m:].tolist(), hi=budget)
    if target is not None:
        row(list(range(m)), [1]*m, lo=target)
    # Network-flow upper bound: new supply can add at most q per AC point.
    # The rounded count cut is valid for the integer AC-only target model.
    # It prevents spending branch-and-bound effort proving fractional point counts impossible.
    if target is not None and not p.dc_enabled and not relaxation:
        no_build, _ = allocate(inst, distance=False)
        needed = max(0, int(np.ceil((target-no_build.sum()-1e-7)/p.q)))
        row(ix.tolist(), [1]*n, lo=needed)
    if np.isfinite(budget) and not relaxation and not p.dc_enabled and min(p.fixed_cost,p.upgrade_cost)>=0:
        row(ix.tolist(), [1]*n, hi=int(np.floor((budget+1e-7)/p.ac_cost)))
    A = coo_matrix((vv, (rr, cc)), shape=(len(lower), nv))
    ub = np.r_[np.full(m, np.inf), inst.maximum, inst.maximum if p.dc_enabled else np.zeros(n), np.ones(2*n)]
    integer = np.r_[np.zeros(m), np.zeros(4*n) if relaxation else np.ones(4*n)]
    return A, np.array(lower), np.array(upper), np.zeros(nv), ub, integer, cap, ann


def optimise(inst, budget=np.inf, target=None, name='solve', relaxation=False, fixed_zero=None, warm_x=None):
    p, n, m = inst.p, inst.n, len(inst.ii)
    A, lo, hi, lb, ub, integer, cap, ann = formulation(inst, budget, target, relaxation)
    if fixed_zero is not None:
        ub[m + np.array(fixed_zero)] = 0
        ub[m+n + np.array(fixed_zero)] = 0
    c = cap / 1000 if target is not None else np.r_[-np.ones(m), np.zeros(4*n)]
    log = OUT / 'solver_logs' / f'{name}.log'
    h = make_solver(c, A, lo, hi, lb, ub, integer, p, log)
    if name == 'base':
        h.writeModel(str(OUT / 'base_model.lp'))
    if warm_x is not None:
        h.setSolution(n, np.arange(m, m+n, dtype=np.int32), np.array(warm_x, dtype=float))
    if target is None and not relaxation:
        initial_flow, _ = allocate(inst, distance=False)
        initial = np.r_[initial_flow, np.zeros(4*n)]
        h.setSolution(len(c), np.arange(len(c),dtype=np.int32), initial)
    if target is not None and not relaxation and not p.dc_enabled:
        # An LP-round-up incumbent is feasible under the integer space and grid bounds.
        # It supplies a reproducible starting solution without claiming LP decisions are buildable.
        lp_solver = make_solver(c, A, lo, hi, lb, ub, np.zeros(len(c)), p)
        relaxed, _ = run(lp_solver, 'target_lp_start')
        if relaxed is not None:
            wx = np.minimum(inst.maximum, np.ceil(relaxed[m:m+n]-1e-7)).astype(int)
            if np.all(wx*p.ac_power <= p.headroom+p.upgrade_kw+1e-7):
                wf, _ = allocate(inst, wx, distance=False)
                wz, wy, _, _ = investments(inst, wx)
                if wf.sum() >= target-1e-5:
                    start_sol = np.r_[wf, wx, np.zeros(n), wz, wy]
                    h.setSolution(len(c), np.arange(len(c),dtype=np.int32), start_sol)
    sol, stage1 = run(h, 'minimum_target_capex' if target is not None else 'maximum_service')
    stages = [stage1]
    if sol is None:
        return {'name': name, 'feasible': False, 'stages': stages, 'budget': budget}
    first_service = float(sol[:m].sum())
    epsilon = max(1e-6, 1e-8 * inst.demand.sum())
    if target is None and not relaxation:
        h.addRow(first_service - epsilon, np.inf, m, np.arange(m, dtype=np.int32), np.ones(m))
        if not p.dc_enabled:
            no_build, _ = allocate(inst, distance=False)
            needed = max(0, int(np.ceil((first_service-epsilon-no_build.sum()-1e-7)/p.q)))
            h.addRow(needed, np.inf, n, np.arange(m,m+n,dtype=np.int32), np.ones(n))
        h.changeColsCost(len(c), np.arange(len(c), dtype=np.int32), ann / 1000)
        h.setSolution(len(sol), np.arange(len(sol), dtype=np.int32), sol)
        candidate, stage2 = run(h, 'minimum_annual_cost')
        stages.append(stage2)
        if candidate is not None:
            sol = candidate
    x, d = sol[m:m+n], sol[m+n:m+2*n]
    if relaxation:
        flow = sol[:m]
        capital, annual = float(cap @ sol), float(ann @ sol)
        z, y = sol[m+2*n:m+3*n], sol[m+3*n:]
    else:
        assert max(np.max(np.abs(x - np.rint(x))), np.max(np.abs(d - np.rint(d)))) < 1e-5
        x, d = np.rint(x).astype(int), np.rint(d).astype(int)
        z, y, capitals, annuals = investments(inst, x, d)
        capital, annual = float(capitals.sum()), float(annuals.sum())
        flow, _ = allocate(inst, x, d)
    result = summarise(inst, x, d, flow, budget, name)
    result.update(feasible=True, capital=capital, annual_cost=annual, stages=stages,
                  first_service=first_service, service_lock_epsilon=epsilon,
                  certified_service=stage1['status'] == 'Optimal',
                  certified_cost=stages[-1]['status'] == 'Optimal', relaxation=relaxation)
    if relaxation:
        result['y'], result['z'] = y, z
        result['site_capital'] = p.ac_cost*x + p.dc_cost*d + p.fixed_cost*z + p.upgrade_cost*y
        result['site_annual'] = p.crf*result['site_capital'] + (p.ac_maintenance+p.network)*x + (p.dc_maintenance+p.network)*d
    return result


def summarise(inst, x, d, flow, budget, name):
    z, y, capital, annual = investments(inst, x, d)
    served_i = np.bincount(inst.ii, weights=flow, minlength=inst.n)
    used_j = np.bincount(inst.jj, weights=flow, minlength=inst.n)
    total = inst.demand.sum()
    return {'name': name, 'budget': float(budget), 'demand': float(total), 'served': float(flow.sum()),
            'service_fraction': float(flow.sum()/total) if total else 1.,
            'capital': float(capital.sum()), 'annual_cost': float(annual.sum()),
            'ac_points': float(x.sum()), 'dc_points': float(d.sum()), 'sites_selected': int(z.sum()),
            'upgrades': int(y.sum()), 'unspent': float(budget - capital.sum()),
            'distance_m': float(inst.distances @ flow / flow.sum()) if flow.sum() else 0,
            'imputed_investment_share': float(capital[inst.sites.imputed].sum()/capital.sum()) if capital.sum() else 0,
            'unallocated_proxy_share': inst.unallocated_proxy_share,
            'x': x, 'dc': d, 'y': y, 'flow': flow, 'served_i': served_i, 'used_j': used_j}


def validate_result(inst, result, tol=1e-4):
    if not result.get('feasible', True):
        return
    x, d, f = result['x'], result['dc'], result['flow']
    _, y, cap, _ = investments(inst, x, d)
    checks = {
        'nonnegative_flows': max(0., -float(f.min(initial=0))),
        'demand_balance': max(0., float((result['served_i'] - inst.demand).max(initial=0))),
        'site_capacity': max(0., float((result['used_j'] - inst.q0 - inst.p.q*x - inst.p.qdc*d).max(initial=0))),
        'space': max(0., float((x+d-inst.maximum).max(initial=0))),
        'power': max(0., float((inst.p.ac_power*x + inst.p.dc_power*d - inst.p.headroom - inst.p.upgrade_kw*y).max(initial=0))),
        'budget': max(0., float(cap.sum() - result['budget'])),
        'integrality': float(max(np.abs(x-np.rint(x)).max(initial=0), np.abs(d-np.rint(d)).max(initial=0))),
    }
    if 'first_service' in result:
        checks['service_lock'] = max(0., result['first_service'] - result['served'] - 2*result['service_lock_epsilon'])
    assert all(v <= tol for v in checks.values()), (result['name'], checks)
    return checks


def save_result(inst, r):
    dest = OUT / 'runs' / r['name']
    dest.mkdir(parents=True, exist_ok=True)
    scalar = {k: v for k, v in r.items() if not isinstance(v, np.ndarray)}
    scalar['parameters'] = asdict(inst.p)
    if r.get('feasible', True) and not r.get('relaxation', False):
        scalar['residual_checks'] = validate_result(inst, r)
    (dest / 'metrics.json').write_text(json.dumps(scalar, indent=2))
    if 'x' not in r:
        return
    s = inst.sites.copy()
    s['demand_kwh_day'], s['served_kwh_day'] = inst.demand, r['served_i']
    s['unmet_kwh_day'] = inst.demand - r['served_i']
    s['existing_capacity'], s['capacity_used'] = inst.q0, r['used_j']
    s['ac_additions'], s['dc_additions'], s['upgrade'] = r['x'], r['dc'], r['y']
    _, _, s['capex'], s['annual_cost'] = investments(inst, r['x'], r['dc'])
    if r.get('relaxation', False):
        s['capex'], s['annual_cost'] = r['site_capital'], r['site_annual']
    s['space_slack'] = inst.maximum - r['x'] - r['dc']
    s['power_slack_kw'] = inst.p.headroom + inst.p.upgrade_kw*r['y'] - inst.p.ac_power*r['x'] - inst.p.dc_power*r['dc']
    s.to_csv(dest / 'site_decisions.csv', index=False)
    pd.DataFrame({'demand_site': s.car_park_no.iloc[inst.ii].to_numpy(), 'supply_site': s.car_park_no.iloc[inst.jj].to_numpy(),
                  'distance_m': inst.distances, 'kwh_day': r['flow']}).query('kwh_day > 1e-8').to_csv(dest / 'demand_flows.csv', index=False)
    s.groupby('area_2019')[['demand_kwh_day', 'served_kwh_day', 'unmet_kwh_day', 'ac_additions', 'dc_additions', 'capex', 'annual_cost']].sum().to_csv(dest / 'area_results.csv')
