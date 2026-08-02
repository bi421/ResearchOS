import pytest
from researchos.validation.prop_validator import TradingRiskCheck

def test_trading_risk_check_success():
    validator = TradingRiskCheck(initial_balance=10000.0)
    result = validator.check_trade_risk(
        current_balance=10000.0,
        daily_low_balance=10000.0,
        risk_amount=50.0,
        reward_amount=150.0
    )
    assert result["is_valid"] is True
    assert result["rr_ratio"] == 3.0

def test_trading_risk_check_failure_rr():
    validator = TradingRiskCheck(initial_balance=10000.0)
    result = validator.check_trade_risk(
        current_balance=10000.0,
        daily_low_balance=10000.0,
        risk_amount=50.0,
        reward_amount=50.0
    )
    assert result["is_valid"] is False
    assert result["rr_passed"] is False