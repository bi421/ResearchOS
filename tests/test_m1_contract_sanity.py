import pytest

from researchos.market_memory.m1_outcome_contract import M1OutcomeContract


def test_m1_contract_is_immutable() -> None:
    contract = M1OutcomeContract()
    with pytest.raises(AttributeError):
        contract.horizon_days = 2
