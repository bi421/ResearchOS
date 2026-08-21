"""Quick start example for ResearchOS."""

from researchos import Research, Observation, Evidence, Hypothesis, Scenario


def main():
    research = Research()

    obs = Observation(
        instrument="BTCUSD",
        timeframe="1h",
        data={"close": 50000.0},
    )
    research.add_observation(obs)

    evidence = Evidence(
        source="price_action",
        data={"trend": "bullish"},
        confidence=0.8,
    )
    research.add_evidence(evidence)

    hypothesis = Hypothesis(
        description="Price will increase",
        evidence=[evidence],
    )
    research.add_hypothesis(hypothesis)

    scenario = Scenario(
        name="Bullish scenario",
        hypotheses=[hypothesis],
    )
    research.add_scenario(scenario)

    print("Quick start completed successfully!")


if __name__ == "__main__":
    main()
