from dataclasses import replace

from oceanic_attestation import Attestation, Authorization, RuntimeState
from oceanic_observer import Observation
from omega_evolution_lineage import propose_with_lineage, to_dict


def attestation() -> Attestation:
    return Attestation(
        schema="oceanic.attestation/v0.1",
        attestation_id="att-2",
        contract_id="contract-1",
        created_at="2026-01-01T00:00:00+00:00",
        adapters=(),
        aggregate={"status": "proved"},
        authorization=Authorization(status="approved", authority="human"),
        runtime=RuntimeState(status="observed", runtime_digest="sha256:runtime"),
    )


def observation(status: str = "deviated") -> Observation:
    return Observation(
        status=status,
        contract_id="contract-1",
        runtime_digest="sha256:runtime",
        expected={"state": "expected"},
        actual={"state": "actual"},
        deviations=("runtime result differs",) if status == "deviated" else (),
    )


def test_evolution_preserves_attestation_lineage_and_proposal():
    lineage = propose_with_lineage(
        attestation(),
        observation(),
        parent_attestation_id="att-1",
        lineage_depth=1,
    )
    assert lineage.attestation_id == "att-2"
    assert lineage.parent_attestation_id == "att-1"
    assert lineage.lineage_depth == 1
    assert lineage.proposal is not None
    assert lineage.proposal.attestation_id == "att-2"


def test_matched_observation_has_no_evolution_proposal():
    lineage = propose_with_lineage(attestation(), observation("matched"))
    assert lineage.proposal is None


def test_parent_requires_positive_depth():
    try:
        propose_with_lineage(attestation(), observation(), parent_attestation_id="att-1")
    except ValueError as exc:
        assert "positive lineage depth" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_serialization_is_explicit_and_stable_shape():
    payload = to_dict(propose_with_lineage(attestation(), observation()))
    assert payload["schema"] == "omega.evolution-lineage/v1"
    assert payload["attestation_id"] == "att-2"
    assert payload["runtime_digest"] == "sha256:runtime"
    assert payload["lineage_depth"] == 0
    assert payload["proposal"]["attestation_id"] == "att-2"
