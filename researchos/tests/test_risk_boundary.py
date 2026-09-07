from __future__ import annotations

import pytest

from researchos.risk import RiskInput, RiskPolicy, TradeStatistics, calculate_risk


def _request(**overrides: object) -> RiskInput:
    values: dict[str, object] = {
        "asset": "XAUUSD",
        "direction": "UP",
        "probability": 0.60,
        "account_equity": 10_000.0,
        "trade_statistics": TradeStatistics(
            average_win=150.0,
            average_loss=100.0,
            sample_size=200,
        ),
    }
    values.update(overrides)
    return RiskInput(**values)  # type: ignore[arg-type]


def test_kelly_is_based_on_probability_and_historical_payoff() -> None:
    result = calculate_risk(_request())

    # b = 150/100 = 1.5; f = .60 - .40/1.5 = 1/3.
    assert result.win_loss_ratio == pytest.approx(1.5)
    assert result.full_kelly_fraction == pytest.approx(1 / 3)
    assert result.fractional_kelly_fraction == pytest.approx(1 / 12)


def test_risk_policy_caps_fractional_kelly() -> None:
    result = calculate_risk(_request())

    assert result.final_risk_fraction == pytest.approx(0.01)
    assert result.risk_amount == pytest.approx(100.0)
    assert result.capped is True


def test_position_size_is_optional_and_derived_from_unit_risk() -> None:
    result = calculate_risk(_request(risk_per_unit=20.0))

    assert result.risk_amount == pytest.approx(100.0)
    assert result.position_size == pytest.approx(5.0)


def test_negative_edge_returns_zero_risk() -> None:
    result = calculate_risk(_request(probability=0.40))

    assert result.full_kelly_fraction == 0.0
    assert result.final_risk_fraction == 0.0
    assert result.risk_amount == 0.0


def test_contract_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError, match="probability"):
        calculate_risk(_request(probability=1.1))


def test_contract_is_versioned_and_serializable() -> None:
    payload = _request(research_id="R-001").to_dict()

    assert payload["schema_version"] == "risk.v1"
    assert payload["research_id"] == "R-001"
    assert payload["trade_statistics"]["sample_size"] == 200


def test_risk_result_is_immutable() -> None:
    result = calculate_risk(_request())

    with pytest.raises(AttributeError):
        result.risk_amount = 999.0  # type: ignore[misc]
