import json
import subprocess
import sys
import unittest
from copy import deepcopy
from scripts.build_so101_shopping import load_data, validate, cost_estimate, disposition
from scripts.project_paths import ROOT


class So101ShoppingTests(unittest.TestCase):
    def test_inventory_reconciles_to_archived_workbook(self):
        plan, inventory = load_data()
        validate(plan, inventory)

    def test_partial_cost_does_not_hide_missing_quotes(self):
        plan, inventory = load_data()
        cost = cost_estimate(plan, inventory)
        self.assertEqual(cost['known_partial_totals'], {'USD':4.99})
        self.assertFalse(cost['complete'])
        self.assertIsNone(cost['delivered_total'])
        self.assertNotIn('N03', cost['unpriced_or_conditional_lines'])
        self.assertEqual(cost['historical_recorded_spend_try'],8774.90)

    def test_ledger_and_quantity_errors_are_rejected(self):
        plan, inventory = load_data()
        for target in ['inventory', 'motors', 'fasteners']:
            p, i = deepcopy(plan), deepcopy(inventory)
            if target == 'inventory': i['rows'].append(deepcopy(i['rows'][0]))
            elif target == 'motors': p['items'][0]['buy_max'] = 2
            else: p['fastener_audit'][0]['m3x6'] += 1
            with self.assertRaises(AssertionError): validate(p,i,verify_source=False)

    def test_all_inventory_rows_have_dispositions(self):
        _, inventory = load_data()
        for r in inventory['rows']:
            self.assertTrue(all(disposition(r['record_id'])))
        self.assertEqual(disposition(36)[0],'12 V HATTINDA KULLANMA')
        self.assertEqual(disposition(8)[0],'MUHASEBE')

    def test_supplier_scenario_is_not_a_complete_or_delivered_quote(self):
        plan, inventory = load_data()
        scenario = cost_estimate(plan, inventory)['supplier_scenarios'][0]
        self.assertEqual(scenario['product_subtotals'], {'TRY':10220.93})
        self.assertFalse(scenario['package_complete'])
        self.assertFalse(scenario['complete'])
        self.assertIsNone(scenario['delivered_total'])

    def test_user_purchase_is_counted_once_and_owned_cable_is_not_reordered(self):
        plan, inventory = load_data()
        validate(plan, inventory)
        cost = cost_estimate(plan, inventory)
        self.assertEqual(cost['user_reported_additions_try'],921.25)
        self.assertEqual(cost['combined_recorded_spend_try'],9696.15)
        self.assertEqual(len(inventory['rows']),66)
        self.assertIsNone(inventory['user_records'][1]['gross_try'])
        self.assertNotIn('N08',cost['unpriced_or_conditional_lines'])
        self.assertEqual(next(i for i in plan['items'] if i['id']=='N08')['buy_max'],0)

    def test_orders_are_not_reordered_or_given_quote_as_paid_cost(self):
        plan, inventory = load_data()
        motor = next(r for r in inventory['user_records'] if r['record_id'] == 69)
        psu = next(r for r in inventory['user_records'] if r['record_id'] == 70)
        self.assertEqual(motor['quantity'], 6)
        self.assertIsNone(motor['gross_try'])
        self.assertEqual(psu['gross_try'],321.25)
        for code in ['N01','N03']:
            self.assertEqual(next(i for i in plan['items'] if i['id']==code)['buy_max'],0)

    def test_publisher_rejects_mixed_cad_action(self):
        p = subprocess.run([sys.executable,'-m','scripts.publish_current','--so101-shopping','--rebuild-cad'],cwd=ROOT,capture_output=True)
        self.assertEqual(p.returncode,2)


if __name__ == '__main__': unittest.main()
