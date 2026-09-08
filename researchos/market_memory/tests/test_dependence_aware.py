import pytest

from researchos.market_memory.dependence_aware import block_bootstrap_mean_ci


def test_block_bootstrap_is_deterministic():
    values = [0.01, 0.02, -0.01, 0.03, 0.00, 0.04, -0.02, 0.01]
    first = block_bootstrap_mean_ci(values, block_size=3, num_resamples=200, seed=42)
    second = block_bootstrap_mean_ci(values, block_size=3, num_resamples=200, seed=42)
    assert first == second
    assert first is not None
    assert first[0] <= first[1]


def test_block_size_one_is_valid_independence_baseline():
    values = [1.0, 2.0, 3.0, 4.0]
    result = block_bootstrap_mean_ci(values, block_size=1, num_resamples=100, seed=7)
    assert result is not None
    assert result[0] <= 2.5 <= result[1]


@pytest.mark.parametrize("block_size", [0, 5])
def test_invalid_block_size_fails_closed(block_size):
    with pytest.raises(ValueError, match="block_size"):
        block_bootstrap_mean_ci([1.0, 2.0, 3.0, 4.0], block_size=block_size)


def test_non_finite_values_fail_closed():
    with pytest.raises(ValueError, match="finite"):
        block_bootstrap_mean_ci([1.0, float("nan"), 2.0], block_size=2)
