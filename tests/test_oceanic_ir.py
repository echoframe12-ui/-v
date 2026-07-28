"""Tests for the Oceanic IR Contract — the language-neutral verification contract.

Covers:
  - Construction with all fields
  - api_version, contract_id, intent are required (ValueError if missing)
  - to_dict round-trip: all fields present and typed correctly
  - from_dict round-trip: produces equivalent contract
  - from_dict with missing optional fields uses empty defaults
  - Immutability (frozen dataclass — assignment raises FrozenInstanceError)
  - inputs/outputs/invariants/effects/bounds/dependencies/proof_obligations/dissent_triggers/risk
"""
import unittest

from oceanic_ir import OceanicIRContract


_FULL = dict(
    api_version="oceanic.ir/v0.1",
    contract_id="ir.test.v1",
    intent="test IR contract construction",
    inputs=({"name": "a", "type": "integer"}, {"name": "b", "type": "integer"}),
    outputs={"type": "integer"},
    invariants=("result == a + b",),
    effects=("log.write",),
    bounds={"time": "O(1)", "memory": "O(1)"},
    dependencies=("stdlib.math",),
    proof_obligations=("arithmetic_correctness", "overflow_handling"),
    dissent_triggers=("overflow",),
    risk={"class": "low", "human_authorization": False},
)


class OceanicIRContractConstructionTests(unittest.TestCase):

    def test_full_contract_constructs_without_error(self):
        c = OceanicIRContract(**_FULL)
        self.assertEqual(c.contract_id, "ir.test.v1")
        self.assertEqual(c.api_version, "oceanic.ir/v0.1")
        self.assertEqual(c.intent, "test IR contract construction")

    def test_missing_api_version_raises_value_error(self):
        with self.assertRaises(ValueError):
            OceanicIRContract(**{**_FULL, "api_version": ""})

    def test_missing_contract_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            OceanicIRContract(**{**_FULL, "contract_id": ""})

    def test_missing_intent_raises_value_error(self):
        with self.assertRaises(ValueError):
            OceanicIRContract(**{**_FULL, "intent": ""})

    def test_contract_is_immutable(self):
        c = OceanicIRContract(**_FULL)
        with self.assertRaises((AttributeError, TypeError)):
            c.contract_id = "mutated"  # type: ignore[misc]

    def test_inputs_stored_as_sequence(self):
        c = OceanicIRContract(**_FULL)
        self.assertEqual(len(c.inputs), 2)
        self.assertEqual(c.inputs[0]["name"], "a")

    def test_proof_obligations_are_accessible(self):
        c = OceanicIRContract(**_FULL)
        self.assertIn("arithmetic_correctness", c.proof_obligations)
        self.assertIn("overflow_handling", c.proof_obligations)

    def test_risk_dict_is_accessible(self):
        c = OceanicIRContract(**_FULL)
        self.assertEqual(c.risk["class"], "low")
        self.assertFalse(c.risk["human_authorization"])


class OceanicIRContractSerializationTests(unittest.TestCase):

    def setUp(self):
        self.contract = OceanicIRContract(**_FULL)

    def test_to_dict_has_all_required_keys(self):
        d = self.contract.to_dict()
        for key in (
            "api_version", "contract_id", "intent", "inputs", "outputs",
            "invariants", "effects", "bounds", "dependencies",
            "proof_obligations", "dissent_triggers", "risk",
        ):
            self.assertIn(key, d)

    def test_to_dict_inputs_are_list(self):
        d = self.contract.to_dict()
        self.assertIsInstance(d["inputs"], list)
        self.assertEqual(len(d["inputs"]), 2)

    def test_to_dict_proof_obligations_are_list(self):
        d = self.contract.to_dict()
        self.assertIsInstance(d["proof_obligations"], list)
        self.assertIn("arithmetic_correctness", d["proof_obligations"])

    def test_from_dict_round_trip_preserves_contract_id(self):
        d = self.contract.to_dict()
        restored = OceanicIRContract.from_dict(d)
        self.assertEqual(restored.contract_id, self.contract.contract_id)
        self.assertEqual(restored.intent, self.contract.intent)
        self.assertEqual(restored.api_version, self.contract.api_version)

    def test_from_dict_round_trip_preserves_proof_obligations(self):
        d = self.contract.to_dict()
        restored = OceanicIRContract.from_dict(d)
        self.assertEqual(set(restored.proof_obligations), set(self.contract.proof_obligations))

    def test_from_dict_with_missing_optional_fields_uses_empty_defaults(self):
        minimal = {
            "api_version": "oceanic.ir/v0.1",
            "contract_id": "minimal.v1",
            "intent": "minimal contract",
        }
        c = OceanicIRContract.from_dict(minimal)
        self.assertEqual(c.contract_id, "minimal.v1")
        self.assertEqual(len(c.inputs), 0)
        self.assertEqual(len(c.proof_obligations), 0)
        self.assertEqual(len(c.dissent_triggers), 0)
        self.assertEqual(len(c.effects), 0)
        self.assertEqual(len(c.dependencies), 0)
        self.assertEqual(c.risk, {})

    def test_from_dict_missing_required_contract_id_raises(self):
        with self.assertRaises((KeyError, ValueError)):
            OceanicIRContract.from_dict({"api_version": "oceanic.ir/v0.1", "intent": "x"})

    def test_to_dict_outputs_is_dict(self):
        d = self.contract.to_dict()
        self.assertIsInstance(d["outputs"], dict)
        self.assertEqual(d["outputs"]["type"], "integer")

    def test_to_dict_risk_is_dict(self):
        d = self.contract.to_dict()
        self.assertIsInstance(d["risk"], dict)
        self.assertEqual(d["risk"]["class"], "low")


if __name__ == "__main__":
    unittest.main()
