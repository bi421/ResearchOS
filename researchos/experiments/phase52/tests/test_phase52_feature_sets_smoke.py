from researchos.experiments.phase52 import MultivariateEmpiricalProbabilityEstimator


def test_multivariate_estimator_imports():
    estimator = MultivariateEmpiricalProbabilityEstimator(feature_indices=(0,), n_neighbors=1)
    assert estimator.n_neighbors == 1
