from verify_stack import verify_live


def test_verify_live_exercises_real_e2e_and_mood():
    result = verify_live()
    assert result.verified is True
    assert all(result.checks.values())
    assert result.mood.status == "clear"
    assert result.mood.route == "continue"
