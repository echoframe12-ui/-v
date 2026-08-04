from full_stack_e2e_gate import check


def test_complete_stack_imports_and_edge_rejects_empty_attestation():
    report = check()
    assert report["ok"], report
    assert report["edge_rejects_empty_attestation"] is True
