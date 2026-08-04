from oceanic_ir import ContractState
from oceanic_ir_vaas_lineage import verify_vaas_lineage


def test_missing_attestation_is_unproven():
    result = verify_vaas_lineage({})
    assert result.status is ContractState.UNPROVEN
    assert set(result.missing_obligations) == {"signature_integrity", "attestation_lineage"}


def test_unsigned_record_cannot_claim_lineage():
    result = verify_vaas_lineage({"attestation_id": "att_root"})
    assert result.status is ContractState.UNPROVEN
    assert "signature_integrity" in result.missing_obligations
    assert "attestation_lineage" not in result.missing_obligations


def test_lineage_requires_nonempty_parent_when_parent_field_is_present():
    result = verify_vaas_lineage({"attestation_id": "att_child", "parent_attestation_id": ""})
    assert result.status is ContractState.UNPROVEN
    assert "attestation_lineage" in result.missing_obligations
