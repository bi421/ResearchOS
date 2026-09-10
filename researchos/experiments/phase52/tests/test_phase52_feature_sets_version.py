from researchos.experiments.phase52 import Phase52Config


def test_feature_set_configuration_is_deterministic():
    assert Phase52Config(n_neighbors=25).n_neighbors == 25
