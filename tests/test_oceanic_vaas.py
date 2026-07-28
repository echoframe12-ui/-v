'''Tests for Oceanic VaaS (Verification-as-a-Service) REST endpoints.

Covers:
  POST /oceanic/contracts        -- contract validation
  POST /oceanic/verify           -- adapter compilation
  POST /oceanic/attest           -- attestation generation (with/without auth)
  POST /oceanic/lifecycle/run    -- full lifecycle (matched + deviated)
  GET  /oceanic/lifecycle/events -- ledger history
  GET  /oceanic/lifecycle/chain/verify -- chain integrity
'''
import json
import unittest

from app import app


_CONTRACT = {
    'api_version': 'oceanic.ir/v0.1',
    'contract_id': 'vaas.test.add.v1',
    'intent': 'combine two numeric values',
    'inputs': [{'name': 'a', 'type': 'integer'}, {'name': 'b', 'type': 'integer'}],
    'outputs': {'type': 'integer'},
    'invariants': ['result == mathematical_sum(a, b)'],
    'effects': [],
    'bounds': {'time': 'O(1)', 'memory': 'O(1)'},
    'dependencies': [],
    'proof_obligations': ['arithmetic_correctness', 'overflow_handling'],
    'dissent_triggers': ['overflow'],
    'risk': {'class': 'low', 'human_authorization': False},
}


class OceanicVaaSContractTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_contract_returns_200(self):
        resp = self.client.post('/oceanic/contracts', data=json.dumps(_CONTRACT), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body['valid'])
        self.assertEqual(body['contract']['contract_id'], 'vaas.test.add.v1')

    def test_missing_required_field_returns_400(self):
        bad = {k: v for k, v in _CONTRACT.items() if k != 'api_version'}
        resp = self.client.post('/oceanic/contracts', data=json.dumps(bad), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.get_json())

    def test_empty_contract_id_returns_400(self):
        bad = dict(_CONTRACT, contract_id='')
        resp = self.client.post('/oceanic/contracts', data=json.dumps(bad), content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class OceanicVaaSVerifyTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_verify_returns_compilation_report(self):
        resp = self.client.post('/oceanic/verify', data=json.dumps(_CONTRACT), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['contract_id'], 'vaas.test.add.v1')
        self.assertEqual(body['adapter_count'], 3)
        self.assertIn('confidence', body)
        self.assertIn('dissent', body)
        self.assertEqual(len(body['adapters']), 3)

    def test_verify_reports_dissent_for_partial_proof(self):
        resp = self.client.post('/oceanic/verify', data=json.dumps(_CONTRACT), content_type='application/json')
        body = resp.get_json()
        self.assertTrue(len(body['dissent']) > 0)

    def test_verify_invalid_contract_returns_400(self):
        resp = self.client.post('/oceanic/verify', data=json.dumps({'intent': 'missing fields'}), content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class OceanicVaaSAttestTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_attest_creates_attestation(self):
        resp = self.client.post('/oceanic/attest', data=json.dumps(_CONTRACT), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body['schema'], 'oceanic.attestation/v0.1')
        self.assertTrue(body['attestation_digest'].startswith('sha256:'))
        self.assertEqual(body['authorization']['status'], 'pending')

    def test_attest_with_reviewer_authorizes_immediately(self):
        payload = dict(_CONTRACT, reviewer='vaas-test-reviewer', reason='Approved for VaaS test.')
        resp = self.client.post('/oceanic/attest', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body['authorization']['status'], 'authorized')

    def test_attest_invalid_contract_returns_400(self):
        resp = self.client.post('/oceanic/attest', data=json.dumps({'bad': 'data'}), content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class OceanicVaaSLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _payload(self, expected=4, execute_value=4):
        return {'contract': _CONTRACT, 'reviewer': 'vaas-reviewer', 'reason': 'Approved for lifecycle REST test.', 'expected': expected, 'execute_value': execute_value}

    def test_matched_lifecycle_run(self):
        resp = self.client.post('/oceanic/lifecycle/run', data=json.dumps(self._payload()), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['observation_status'], 'matched')
        self.assertEqual(body['authorization_status'], 'authorized')
        self.assertIsNone(body['evolution'])
        self.assertTrue(body['attestation_digest'].startswith('sha256:'))

    def test_deviated_lifecycle_produces_evolution_proposal(self):
        resp = self.client.post('/oceanic/lifecycle/run', data=json.dumps(self._payload(expected=4, execute_value=99)), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['observation_status'], 'deviated')
        self.assertIsNotNone(body['evolution'])
        self.assertEqual(body['evolution']['category'], 'contract_runtime_deviation')
        self.assertTrue(body['evolution']['requires_human_review'])

    def test_missing_reviewer_returns_400(self):
        payload = self._payload()
        del payload['reviewer']
        resp = self.client.post('/oceanic/lifecycle/run', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_missing_reason_returns_400(self):
        payload = self._payload()
        del payload['reason']
        resp = self.client.post('/oceanic/lifecycle/run', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_lifecycle_events_endpoint(self):
        self.client.post('/oceanic/lifecycle/run', data=json.dumps(self._payload()), content_type='application/json')
        resp = self.client.get('/oceanic/lifecycle/events')
        self.assertEqual(resp.status_code, 200)
        events = resp.get_json()
        self.assertIsInstance(events, list)
        types = [e['event_type'] for e in events]
        self.assertIn('contract.created', types)

    def test_lifecycle_chain_verify_endpoint(self):
        resp = self.client.get('/oceanic/lifecycle/chain/verify')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('intact', body)
        self.assertIn('event_count', body)
        self.assertTrue(body['intact'])

    def test_lifecycle_events_limit_param(self):
        self.client.post('/oceanic/lifecycle/run', data=json.dumps(self._payload()), content_type='application/json')
        resp = self.client.get('/oceanic/lifecycle/events?limit=2')
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(resp.get_json()), 2)


if __name__ == '__main__':
    unittest.main()


class OceanicDriftStatsTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_drift_stats_empty_returns_zero(self):
        resp = self.client.get('/oceanic/drift/stats')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn('total_audits', body)
        self.assertIn('deviated', body)
        self.assertIn('intact', body)
        self.assertIn('deviated_ratio', body)
        self.assertIn('latest', body)
        self.assertIn('history', body)

    def test_drift_stats_limit_param_invalid_returns_400(self):
        resp = self.client.get('/oceanic/drift/stats?limit=bad')
        self.assertEqual(resp.status_code, 400)

    def test_drift_stats_after_deviated_lifecycle(self):
        payload = {
            'contract': {
                'api_version': 'oceanic.ir/v0.1',
                'contract_id': 'vaas.drift.test.v1',
                'intent': 'drift test',
                'inputs': [{'name': 'a', 'type': 'integer'}],
                'outputs': {'type': 'integer'},
                'invariants': ['result == a'],
                'effects': [],
                'bounds': {'time': 'O(1)', 'memory': 'O(1)'},
                'dependencies': [],
                'proof_obligations': ['arithmetic_correctness'],
                'dissent_triggers': [],
                'risk': {'class': 'low', 'human_authorization': False},
            },
            'reviewer': 'drift-reviewer',
            'reason': 'Drift deviation test.',
            'expected': 1,
            'execute_value': 999,
        }
        run_resp = self.client.post('/oceanic/lifecycle/run', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(run_resp.status_code, 200)
        self.assertEqual(run_resp.get_json()['observation_status'], 'deviated')

        stats_resp = self.client.get('/oceanic/drift/stats')
        body = stats_resp.get_json()
        self.assertGreater(body['deviated'], 0)
        self.assertGreater(body['total_audits'], 0)


class OceanicPerspectivesTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    _CONTRACT = {
        'api_version': 'oceanic.ir/v0.1',
        'contract_id': 'vaas.perspectives.test.v1',
        'intent': 'perspectives test',
        'inputs': [{'name': 'a', 'type': 'integer'}, {'name': 'b', 'type': 'integer'}],
        'outputs': {'type': 'integer'},
        'invariants': ['result == a + b'],
        'effects': [],
        'bounds': {'time': 'O(1)', 'memory': 'O(1)'},
        'dependencies': [],
        'proof_obligations': ['arithmetic_correctness', 'overflow_handling'],
        'dissent_triggers': ['overflow'],
        'risk': {'class': 'low', 'human_authorization': False},
    }

    def test_perspectives_returns_comparison(self):
        resp = self.client.post('/oceanic/perspectives', data=json.dumps(self._CONTRACT), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['contract_id'], 'vaas.perspectives.test.v1')
        self.assertIn('aggregate_confidence', body)
        self.assertIn('dissent_flag', body)
        self.assertIn('context_hash', body)
        self.assertEqual(len(body['perspectives']), 3)
        self.assertIn('comparison', body)
        self.assertTrue(body['dissent_flag'])  # python/ts can't prove overflow_handling

    def test_perspectives_invalid_contract_returns_400(self):
        resp = self.client.post('/oceanic/perspectives', data=json.dumps({'bad': 'payload'}), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_perspectives_no_dissent_when_all_supported(self):
        # A contract that all adapters can prove (only arithmetic_correctness)
        simple = dict(self._CONTRACT, contract_id='vaas.perspectives.nodissent.v1', proof_obligations=['arithmetic_correctness'], dissent_triggers=[])
        resp = self.client.post('/oceanic/perspectives', data=json.dumps(simple), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertFalse(body['dissent_flag'])  # all 3 adapters support arithmetic_correctness
