"""Small independent expected-answer checks, plus source-data reconciliation."""
import unittest
from dataclasses import replace
import numpy as np
import pandas as pd
from model import Parameters, Instance, optimise, allocate, build_instance, validate_result
from prepare_data import INPUTS, address_parts
from baselines import greedy_rule


def tiny(demand=(5., 5.), shared=True, max_points=3):
    s = pd.DataFrame({'car_park_no': ['A', 'B'], 'imputed': [False, False], 'lots': [10, 10]})
    p = Parameters(ac_power=1, hours=4, availability=1, power_factor=1,
                   ac_cost=3, headroom=1, upgrade_kw=2, upgrade_cost=5,
                   fixed_cost=0, ac_maintenance=0, network=0, time_limit=10, mip_gap=0)
    ii, jj = np.array([(0, 0), (0, 1), (1, 0), (1, 1)] if shared else [(0, 0), (1, 1)]).T
    return Instance(s, p, np.array(demand), np.array([4., 0.]), np.array([1., 0.]),
                    np.array([max_points, 0]), ii, jj, np.where(ii==jj, 0., 100.))


class ModelTests(unittest.TestCase):
    def test_hand_solved_upgrade_integrality(self):
        i = tiny()
        # Initial 4; one point costs 3 and serves 8; two cost 11 and serve all 10.
        for budget, served, count in [(0, 4, 0), (3, 8, 1), (10, 8, 1), (11, 10, 2)]:
            r = optimise(i, budget=budget, name=f'test_tiny_{budget}')
            self.assertAlmostEqual(r['served'], served, places=4)
            self.assertEqual(r['x'].sum(), count)
            validate_result(i, r)

    def test_disconnected_node_remains_unmet(self):
        i = tiny(shared=False)
        i.ii, i.jj, i.distances = np.array([0]), np.array([0]), np.array([0.])
        r = optimise(i, budget=100, name='test_disconnected')
        self.assertAlmostEqual(r['served'], 5, places=4)
        self.assertEqual(r['served_i'][1], 0)

    def test_zero_demand_buys_nothing(self):
        r = optimise(tiny((0., 0.)), budget=100, name='test_zero_demand')
        self.assertEqual(r['capital'], 0)

    def test_infeasible_target(self):
        r = optimise(tiny(shared=False), target=9., name='test_infeasible')
        self.assertFalse(r['feasible'])
        self.assertEqual(r['stages'][0]['status'], 'Infeasible')

    def test_monotonic_cost_capacity_and_lp_bound(self):
        i = tiny()
        r = optimise(i, budget=6, name='test_integer')
        lp = optimise(i, budget=6, name='test_relaxation', relaxation=True)
        self.assertGreaterEqual(lp['served']+1e-5, r['served'])
        cheaper = replace(i, p=replace(i.p, ac_cost=1, upgrade_cost=0))
        self.assertGreaterEqual(optimise(cheaper, budget=6, name='test_cheap')['served']+1e-5, r['served'])
        capacity = replace(i, q0=i.q0+3)
        self.assertGreaterEqual(allocate(capacity)[0].sum(), allocate(i)[0].sum())

    def test_greedy_step_upgrade(self):
        r, trace = greedy_rule(tiny(), 11)
        self.assertAlmostEqual(r['served'], 10, places=4)
        self.assertEqual([t['step_capex'] for t in trace], [3, 8])

    def test_fixed_site_cost_and_dc_choice(self):
        i=tiny()
        activated=replace(i,p=replace(i.p,fixed_cost=2))
        r=optimise(activated,budget=3,name='test_activation_cost')
        self.assertEqual(r['x'].sum(),0)
        dc=replace(i,p=replace(i.p,dc_enabled=True,dc_power=2,dc_hours=4,
                              dc_power_factor=1,dc_cost=4,dc_maintenance=0))
        r=optimise(dc,budget=9,name='test_dc_choice')
        self.assertEqual(r['dc'].sum(),1)
        self.assertEqual(r['x'].sum(),0)
        self.assertAlmostEqual(r['served'],10,places=4)
        self.assertEqual(r['capital'],9)
        validate_result(dc,r)

    def test_source_reconciliation(self):
        i = build_instance()
        s = i.sites
        c = pd.read_csv(INPUTS / 'hdb_charger_crosswalk.csv')
        self.assertEqual(len(s), 2273)
        self.assertEqual(int(s.imputed.sum()), 278)
        self.assertEqual(s.total_lots.sum(), 706663)
        self.assertTrue(c.evCpId.is_unique)
        self.assertEqual(len(c), 11489)
        a = pd.read_csv(INPUTS / 'area_demand_weights.csv')
        for y in (2025, 2026):
            stock = a[(a.year==y)&(a.metric=='dwellings')].value.sum()
            self.assertTrue(1e6 < stock < 1.5e6, stock)
        self.assertTrue(np.isfinite(i.demand).all())
        expected = i.p.stock * i.p.hdb_share * i.p.dependence * i.p.annual_km/365*i.p.intensity/i.p.efficiency
        self.assertAlmostEqual(i.demand.sum(), expected)
        self.assertEqual(set(zip(i.ii[i.ii==i.jj],i.jj[i.ii==i.jj])), {(j,j) for j in range(i.n)})

    def test_address_parser(self):
        b, s, r = address_parts('BLK 720-727,730-731 CLEMENTI WEST STREET 2')
        self.assertEqual(s, 'CLEMENTI WEST STREET 2')
        self.assertEqual(b, {'720','727','730','731'})
        self.assertIn((720,727),r)


if __name__ == '__main__':
    unittest.main(verbosity=2)
