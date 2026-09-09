import pytest

from researchos.market_memory.m1_outcome_contract import M1OutcomeContract


def test_contract_defaults_are_explicit() -> None:
    contract = M1OutcomeContract()
    assert contract.horizon_days == 1
    assert contract.threshold_return == 0.0
    assert contract.price_field == "close"
    assert contract.direction_aware is True
    assert contract.label_name == "hit_threshold_1d"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizon_days": 0},
        {"threshold_return": -0.001},
        {"price_field": "open"},
        {"direction_aware": False},
    ],
)
def test_contract_rejects_ambiguous_label_definitions(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        M1OutcomeContract(**kwargs)
