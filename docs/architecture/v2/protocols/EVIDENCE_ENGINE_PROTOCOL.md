\# ResearchOS v2 — Evidence Engine Protocol



Version: 2.0

Status: Architecture Design



\---



\# 1. Purpose



Evidence Engine is responsible for collecting,

tracking, validating and ranking evidence.



The system does not accept conclusions without evidence.



Every intelligence output must have:



\- source

\- timestamp

\- confidence

\- validation status

\- provenance



\---



\# 2. Evidence Flow



INPUT



Question



↓



Evidence Search



↓



Evidence Collection



↓



Evidence Validation



↓



Evidence Ranking



↓



Reasoning Layer



↓



Decision Layer





\---



\# 3. Evidence Object



Every evidence object contains:



