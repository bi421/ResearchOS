import os

from researchos.agents.tools import ResearchOSAgentTools
from researchos.pipeline import ResearchPipeline
from researchos.storage.repository import ResearchRepository


def run_system_demo():
    print("==================================================")
    print("      ResearchOS End-to-End System Demo           ")
    print("==================================================")

    db_file = "demo_researchos.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    repo = ResearchRepository(db_path=db_file)
    pipeline = ResearchPipeline(repo)
    agent_tools = ResearchOSAgentTools(db_path=db_file)

    print("\n[+] Step 1: Executing Research Cycle via Pipeline...")
    topic = "Multi-Agent Swarm Intelligence"
    research = pipeline.start_research(question=topic)
    print(f" -> Research Created with ID: {research.id}")

    print("\n[+] Step 2: Recording Cryptographic Audit Entry...")
    audits = repo.load_by_type("AuditEntry")
    if audits:
        ae_hash = audits[-1].get("entry_hash", "N/A")
        print(f" -> Last Audit Entry Hash: {ae_hash[:16]}...")
    else:
        print(" -> No audit entries found")

    print("\n[+] Step 3: Simulating AI Agent Tool Invocation...")
    agent_result = agent_tools.run_research_cycle_tool(topic="Algorithmic Risk Management")
    print(f" -> Agent Tool Output: {agent_result}")

    print("\n[+] Step 4: Verifying Audit Chain Cryptographic Integrity...")
    is_valid = repo.verify_audit_chain()
    if is_valid:
        print(" -> Audit Chain Status: [SECURE & VALID]")
    else:
        print(" -> Audit Chain Status: [COMPROMISED]")

    print("\n==================================================")
    print("      ResearchOS Demo Completed Successfully!     ")
    print("==================================================")


if __name__ == "__main__":
    run_system_demo()
