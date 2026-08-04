from mood import MoodSignal, assess


def test_mood_clear_signal():
    result = assess([MoodSignal("readiness", True, "deployment", 1.0)])
    assert result.status == "clear"
    assert result.route == "continue"
    assert result.requires_human is False


def test_mood_surfaces_dissent():
    result = assess([
        MoodSignal("readiness", True, "service-a", 0.9),
        MoodSignal("readiness", False, "service-b", 0.9),
    ])
    assert result.status == "dissent"
    assert "dissent:readiness" in result.gaps
    assert result.route == "human"
    assert result.requires_human is True


def test_mood_surfaces_low_confidence():
    result = assess([MoodSignal("decision", "unknown", "observer", 0.2)])
    assert result.status == "dissent"
    assert "low-confidence:decision" in result.gaps
    assert result.requires_human is True


def test_mood_surfaces_invalid_confidence():
    result = assess([MoodSignal("decision", "unknown", "observer", 1.5)])
    assert result.status == "dissent"
    assert "invalid-confidence:decision" in result.gaps
    assert result.requires_human is True


def test_record_to_ledger(tmp_path):
    from mood import record_to_ledger
    from oceanic_event_ledger import EventLedger

    ledger_file = tmp_path / "test_mood_ledger.jsonl"
    ledger = EventLedger(ledger_file)

    clear_assessment = assess([MoodSignal("readiness", True, "deployment", 1.0)])
    event1 = record_to_ledger(clear_assessment, ledger, entity_id="test-clear")
    assert event1.event_type == "mood.clear"
    assert event1.payload["status"] == "clear"

    dissent_assessment = assess([MoodSignal("readiness", False, "deployment", 1.0)])
    event2 = record_to_ledger(dissent_assessment, ledger, entity_id="test-dissent")
    assert event2.event_type == "mood.dissent"
    assert event2.payload["status"] == "dissent"

    assert ledger.verify_chain() is True
    history = ledger.history()
    assert len(history) == 2

