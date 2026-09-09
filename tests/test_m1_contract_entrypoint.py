from researchos.market_memory.m1_contract import (
    M1OutcomeContract,
    extract_xauusd_m1_sma_crossover_events,
)


def test_m1_contract_entrypoint_exports() -> None:
    assert M1OutcomeContract().label_name == "hit_threshold_1d"
    assert callable(extract_xauusd_m1_sma_crossover_events)
