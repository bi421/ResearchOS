import json
from researchos.pipeline import ResearchPipeline
from researchos.storage.repository import ResearchRepository
from researchos.validation.prop_validator import TradingRiskCheck


class ResearchOSAgentTools:
    """ResearchOS Core Tools designed for AI Agents to execute autonomous research workflows."""

    def __init__(self, db_path: str = "researchos.db", initial_balance: float = 100000.0):
        self.repo = ResearchRepository(db_path=db_path)
        self.pipeline = ResearchPipeline(self.repo)
        self.risk_check = TradingRiskCheck(initial_balance=initial_balance)

    def run_research_cycle_tool(self, topic: str) -> str:
        try:
            research = self.pipeline.start_research(question=topic)

            return json.dumps({
                "status": "success",
                "research_id": research.id,
                "topic": topic,
                "summary": "Research cycle completed",
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def verify_audit_chain_tool(self) -> str:
        is_valid = self.repo.verify_audit_chain()
        return json.dumps({
            "audit_chain_valid": is_valid,
            "status": "SECURE" if is_valid else "COMPROMISED"
        }, ensure_ascii=False)

    def check_trade_risk_tool(self, current_balance: float, daily_low_balance: float, risk_amount: float, reward_amount: float) -> str:
        """External trading risk check — NOT ResearchOS Article XII validation."""
        try:
            result = self.risk_check.check_trade_risk(
                current_balance=current_balance,
                daily_low_balance=daily_low_balance,
                risk_amount=risk_amount,
                reward_amount=reward_amount
            )
            return json.dumps({
                "status": "success",
                "result": result
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_tool_definitions(self) -> list:
        return [
            {
                "name": "run_research_cycle_tool",
                "description": "Execute an autonomous research cycle on a specific technical, scientific, or market topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "The subject matter to research."}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "verify_audit_chain_tool",
                "description": "Check the cryptographic hash chaining and integrity of the system audit logs.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "check_trade_risk_tool",
                "description": "External trading risk check — NOT ResearchOS validation. Checks prop firm drawdown and risk parameters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_balance": {"type": "number"},
                        "daily_low_balance": {"type": "number"},
                        "risk_amount": {"type": "number"},
                        "reward_amount": {"type": "number"}
                    },
                    "required": ["current_balance", "daily_low_balance", "risk_amount", "reward_amount"]
                }
            }
        ]
