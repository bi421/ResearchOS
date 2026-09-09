from researchos.market_memory.m1_outcome_contract import M1OutcomeContract


def test_m1_contract_label_is_stable() -> None:
    assert M1OutcomeContract(horizon_days=1, threshold_return=0.001).label_name == "hit_threshold_1d"
