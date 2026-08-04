from mood import MoodSignal, assess


def test_failed_signal_is_dissent_and_human_routed():
    result = assess([MoodSignal("integrity", False, "test")])
    assert result.status == "dissent"
    assert result.route == "human"
    assert "failed:integrity" in result.gaps


def test_all_clear_signals_continue():
    result = assess([
        MoodSignal("deployment", True, "test"),
        MoodSignal("smoke", True, "test"),
        MoodSignal("integrity", True, "test"),
    ])
    assert result.status == "clear"
    assert result.route == "continue"
