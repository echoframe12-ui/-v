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
