"""Idempotency, partial-run and receipt-alias regressions."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('planner', Path(__file__).parents[1] / 'scripts/plan_import.py')
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


class PlannerTests(unittest.TestCase):
    def fixture(self):
        return {'sources': [{'source_key': 'tricount:r:u', 'source_uuid': 'u', 'upstream_id': 'i',
                             'fingerprint': 'f', 'receipt_keys': ['lidl:123']}],
                'existing_lines': [], 'ledger': []}

    def action(self, data):
        return planner.plan(data)[0]['action']

    def test_first_import_then_idempotent(self):
        data = self.fixture()
        self.assertEqual(self.action(data), 'new')
        data['existing_lines'] = [{'source_key': 'tricount:r:u', 'receipt_keys': ['lidl:123']}]
        self.assertEqual(self.action(data), 'reconcile_existing')
        data['ledger'] = [{'source_key': 'tricount:r:u', 'state': 'Importato verificato', 'fingerprint': 'f'}]
        self.assertEqual(self.action(data), 'skip')
        data['sources'][0]['fingerprint'] = 'changed'
        self.assertEqual(self.action(data), 'review_changed')

    def test_legacy_both_id_namespaces(self):
        for alias in ['u', 'i']:
            data = self.fixture()
            data['existing_lines'] = [{'legacy_transaction_id': alias}]
            self.assertEqual(self.action(data), 'reconcile_existing')

    def test_missing_is_retryable_and_partial_is_not_new(self):
        data = self.fixture()
        data['ledger'] = [{'source_key': 'tricount:r:u', 'state': 'Scontrino mancante'}]
        self.assertEqual(self.action(data), 'retry_pending')
        data['existing_lines'] = [{'source_key': 'tricount:r:u'}]
        self.assertEqual(self.action(data), 'reconcile_existing')

    def test_receipt_prevents_cross_source_duplication(self):
        data = self.fixture()
        data['existing_lines'] = [{'source_key': 'lidl:123', 'receipt_keys': ['lidl:123']}]
        self.assertEqual(self.action(data), 'review_receipt_link')
        data['existing_lines'] = []
        data['sources'].append(dict(data['sources'][0], source_key='tricount:other:u2'))
        self.assertTrue(all(x['action'] == 'review_receipt_link' for x in planner.plan(data)))

    def test_ledger_without_lines_and_disappeared_source(self):
        data = self.fixture()
        data['ledger'] = [{'source_key': 'tricount:r:u', 'state': 'Importato verificato', 'fingerprint': 'f'}]
        self.assertEqual(self.action(data), 'review_missing_lines')
        data['sources'] = []
        self.assertEqual(self.action(data), 'review_absent_source')

    def test_reject_duplicate_source_keys(self):
        data = self.fixture()
        data['sources'] *= 2
        with self.assertRaises(ValueError):
            planner.plan(data)


if __name__ == '__main__':
    unittest.main()
