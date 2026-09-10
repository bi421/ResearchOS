from researchos.experiments.phase52 import Phase52Config


def test_default_feature_set_is_macro_conditioned():
    assert Phase52Config().feature_set == "PRICE + DXY"
