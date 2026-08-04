from oceanic_ir import ContractState
from oceanic_ir_attestation_contract import contract, proof_from_attestation, verify_attestation_contract


def test_contract_is_canonical_and_unproven_without_attestation_evidence():
    result = verify_attestation_contract({})
    assert contract().contract_id == "omega-edge-attestation-v1"
    assert result.status is ContractState.UNPROVEN
    assert set(result.missing_obligations) == {"attestation_signature", "attestation_lineage"}


def test_proof_adapter_maps_both_required_obligations():
    proof = proof_from_attestation({"signature": "sig", "lineage": "root"})
    assert proof.contract_id == contract().contract_id
    assert {claim.obligation for claim in proof.claims} == {
        "attestation_signature",
        "attestation_lineage",
    }


def test_contract_is_deterministic_for_same_input():
    first = verify_attestation_contract({"signature": "sig", "lineage": "root"})
    second = verify_attestation_contract({"signature": "sig", "lineage": "root"})
    assert first == second
