from researchos.market_memory.m1_outcome_contract import M1OutcomeContract


def test_m1_contract_carries_explicit_label_definition() -> None:
    contract = M1OutcomeContract(horizon_days=1, threshold_return=0.0)
    assert contract.direction_aware
    assert contract.price_field == "close"
    assert contract.label_name == "hit_threshold_1d"
