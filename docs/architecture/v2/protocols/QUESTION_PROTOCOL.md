\# ResearchOS v2 — Question Protocol



Version: 2.0



Status: Architecture Specification



Protocol: Question Generation and Decomposition





\# 1. Purpose



The Question Protocol defines how ResearchOS transforms a broad problem into a structured research question.



The system does not immediately answer.



The system first determines:



\- What is being asked?

\- What information is missing?

\- What evidence is required?

\- What assumptions exist?

\- What alternative explanations are possible?





\# 2. Core Principle



A high quality answer begins with a high quality question.



ResearchOS follows:



INPUT PROBLEM



↓



QUESTION ANALYSIS



↓



QUESTION DECOMPOSITION



↓



EVIDENCE REQUIREMENT



↓



RESEARCH TASK





\# 3. Question Object





Every question must contain:





\## question\_id



Unique identifier.





\## original\_question



The initial user or system question.





\## normalized\_question



A clearer technical version of the question.





\## domain



Research category.



Examples:



\- market

\- economics

\- statistics

\- engineering

\- technology





\## objective



The expected outcome.



Examples:



\- explain

\- compare

\- predict

\- verify

\- evaluate





\## constraints



Known limitations.





\# 4. Internal Question Generation





For every question ResearchOS generates internal checks:





\## Q1 — Definition



What exactly is the problem?





\## Q2 — Evidence



What facts are required?





\## Q3 — Assumptions



What assumptions are being made?





\## Q4 — Alternatives



What other explanations exist?





\## Q5 — Verification



How can the conclusion be tested?





\## Q6 — Uncertainty



What remains unknown?





\# 5. Question Decomposition





Complex questions are divided into:





Main Question



↓



Sub Question 1



↓



Sub Question 2



↓



Sub Question 3





Each sub-question must have:



\- purpose

\- required evidence

\- expected output





\# 6. Question Quality Rules





A valid question must be:





\## Specific



Avoid vague objectives.





\## Testable



Must allow verification.





\## Evidence-based



Must define required proof.





\## Bounded



Must define scope.





\# 7. Self-Interview Mechanism





ResearchOS may generate internal research dialogue:





SYSTEM QUESTION:



What do we need to prove?





SYSTEM ANSWER:



Required evidence identified.





SYSTEM QUESTION:



What could make this conclusion wrong?





SYSTEM ANSWER:



Alternative hypothesis generated.





SYSTEM QUESTION:



How can this be verified?





SYSTEM ANSWER:



Validation method selected.





This is not free-form conversation.



It is a controlled reasoning procedure.





\# 8. Output





Question Protocol produces:





Research Question



\+



Evidence Requirements



\+



Research Plan



\+



Verification Criteria





\# 9. Restrictions





The Question Layer must not:





\- invent evidence

\- create unsupported assumptions

\- skip verification

\- produce final decisions





Decision authority belongs to later layers.





END OF QUESTION PROTOCOL

