from researchos.experiments.phase52 import FEATURE_SET_NAMES


def test_feature_set_contract_is_fixed():
    assert FEATURE_SET_NAMES == (
        "PRICE_ONLY",
        "PRICE + DXY",
        "PRICE + US10Y",
        "PRICE + VIX",
        "PRICE + ALL",
    )
