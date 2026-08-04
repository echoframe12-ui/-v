from omega_observer_lineage import ObserverLineage


def test_observer_lineage_module_contract_is_importable():
    assert ObserverLineage.__annotations__["lineage_depth"] is int
