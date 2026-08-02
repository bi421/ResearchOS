"""
WARNING: This module performs TRADING RISK calculations.
It is NOT part of the ResearchOS Article XII Validation Engine.
ResearchOS Validation means: research prediction vs reality comparison.
This utility is kept for external tool use only and is excluded
from the ResearchOS constitutional object model.
"""


class TradingRiskCheck:
    """
    External trading risk check — NOT ResearchOS Article XII validation.

    This is a standalone utility for prop-firm risk parameter checking.
    It is deliberately separated from the ResearchOS validation framework
    and does NOT inherit from BaseObject or use the ResearchOS lifecycle.
    """

    def __init__(self, initial_balance: float, max_daily_dd_pct: float = 5.0, max_total_dd_pct: float = 10.0, max_risk_per_trade_pct: float = 1.0):
        self.initial_balance = initial_balance
        self.max_daily_dd_pct = max_daily_dd_pct
        self.max_total_dd_pct = max_total_dd_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct

    def check_trade_risk(self, current_balance: float, daily_low_balance: float, risk_amount: float, reward_amount: float) -> dict:
        daily_dd = ((self.initial_balance - daily_low_balance) / self.initial_balance) * 100
        daily_passed = daily_dd <= self.max_daily_dd_pct

        total_dd = ((self.initial_balance - current_balance) / self.initial_balance) * 100
        total_passed = total_dd <= self.max_total_dd_pct

        trade_risk_pct = (risk_amount / current_balance) * 100
        risk_passed = trade_risk_pct <= self.max_risk_per_trade_pct

        rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        rr_passed = rr_ratio >= 2.0

        is_valid = daily_passed and total_passed and risk_passed and rr_passed

        return {
            "is_valid": is_valid,
            "daily_drawdown_pct": round(daily_dd, 2),
            "daily_passed": daily_passed,
            "total_drawdown_pct": round(total_dd, 2),
            "total_passed": total_passed,
            "trade_risk_pct": round(trade_risk_pct, 2),
            "risk_passed": risk_passed,
            "rr_ratio": round(rr_ratio, 2),
            "rr_passed": rr_passed
        }