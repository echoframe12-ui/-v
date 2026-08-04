from types import SimpleNamespace

from mood_integrity import assess_e2e, assess_full_stack


def test_e2e_clear_evidence_continues():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
        contract_stack={"ok": True, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "clear"
    assert assessment.route == "continue"
    assert assessment.requires_human is False


def test_e2e_failed_integrity_routes_human():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=False,
        contract_stack={"ok": True, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert assessment.requires_human is True


def test_e2e_failed_contract_stack_routes_human():
    result = SimpleNamespace(
        deployment={"ready": True},
        smoke_ready=True,
        status_code=200,
        request_id="production-smoke",
        integrity=True,
        contract_stack={"ok": False, "edge_rejects_empty_attestation": True},
    )
    assessment = assess_e2e(result)
    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert "failed:contract_stack_healthy" in assessment.gaps


def test_assess_full_stack_integration():
    from app import app

    client = app.test_client()
    assessment = assess_full_stack(client, db_path="oceanicos.db", workspace="workspace")
    assert assessment.status in ("clear", "dissent")
    assert hasattr(assessment, "route")


def test_assess_full_stack_with_ledger(tmp_path):
    from app import app
    from oceanic_event_ledger import EventLedger

    ledger_file = tmp_path / "ledger.jsonl"
    ledger = EventLedger(ledger_file)
    client = app.test_client()
    assessment = assess_full_stack(client, db_path="oceanicos.db", workspace="workspace", ledger=ledger)
    assert assessment.status in ("clear", "dissent")
    history = ledger.history()
    assert len(history) == 1
    assert history[0].event_type == f"mood.{assessment.status}"
    assert history[0].entity_id == "full-stack-e2e"
    assert ledger.verify_chain() is True


def test_assess_perspectives_agreed():
    from mood_integrity import assess_perspectives
    from perspectives import MockPerspectiveAdapter
    from context_assembly import ContextAssembler, ContextSource

    assembler = ContextAssembler()
    ctx = assembler.assemble([ContextSource(ref="r1", content="verify prompt")])
    p1 = MockPerspectiveAdapter("provider-a", "m1", response="approve").generate(ctx)
    p2 = MockPerspectiveAdapter("provider-b", "m2", response="approve").generate(ctx)

    assessment = assess_perspectives([p1, p2])
    assert assessment.status == "clear"
    assert assessment.route == "continue"


def test_assess_perspectives_dissent(tmp_path):
    from mood_integrity import assess_perspectives
    from perspectives import MockPerspectiveAdapter
    from context_assembly import ContextAssembler, ContextSource
    from oceanic_event_ledger import EventLedger

    assembler = ContextAssembler()
    ctx = assembler.assemble([ContextSource(ref="r2", content="verify prompt dissent")])
    p1 = MockPerspectiveAdapter("provider-a", "m1", response="approve").generate(ctx)
    p2 = MockPerspectiveAdapter("provider-b", "m2", response="revise").generate(ctx)

    ledger = EventLedger(tmp_path / "persp_ledger.jsonl")
    assessment = assess_perspectives([p1, p2], ledger=ledger, entity_id="test-panel")

    assert assessment.status == "dissent"
    assert assessment.route == "human"
    assert "dissent:response" in assessment.gaps
    history = ledger.history()
    assert len(history) == 1
    assert history[0].event_type == "mood.dissent"
    assert history[0].entity_id == "test-panel"



