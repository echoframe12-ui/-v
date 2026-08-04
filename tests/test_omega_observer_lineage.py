from typing import get_type_hints

from omega_observer_lineage import ObserverLineage


def test_observer_lineage_module_contract_is_importable():
    assert get_type_hints(ObserverLineage)["lineage_depth"] is int
