from observer import Observation
from omega_becoming_lineage import advance_with_lineage, to_dict


def observation():
    return Observation(
        state="authorized",
        verification_status="verified",
        authorization_level="act",
        confidence=1.0,
        dissent=False,
        provenance=("attestation-1",),
        verification_hash="hash-1",
        attested=True,
        next_state="act_then_observe",
    )


def test_becoming_preserves_attestation_lineage():
    result = advance_with_lineage(
        observation(),
        attestation_id="attestation-2",
        parent_attestation_id="attestation-1",
        lineage_depth=1,
    )
    assert result.attestation_id == "attestation-2"
    assert result.parent_attestation_id == "attestation-1"
    assert result.lineage_depth == 1
    assert result.transition.verification_hash == "hash-1"


def test_parent_requires_positive_depth():
    try:
        advance_with_lineage(
            observation(),
            attestation_id="attestation-2",
            parent_attestation_id="attestation-1",
        )
    except ValueError as exc:
        assert "positive lineage depth" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_serialization_keeps_transition_and_lineage():
    result = advance_with_lineage(observation(), attestation_id="attestation-1")
    payload = to_dict(result)
    assert payload["attestation_id"] == "attestation-1"
    assert payload["lineage_depth"] == 0
    assert payload["transition"]["verification_hash"] == "hash-1"
