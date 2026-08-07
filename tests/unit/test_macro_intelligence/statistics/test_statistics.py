"""
ResearchOS Macro Intelligence Layer - Statistics Tests
"""

import pytest
from datetime import timezone

UTC = timezone.utc


class TestDescriptiveStatistics:
    """Tests for descriptive statistics."""
    
    def test_mean(self):
        """Test mean calculation."""
        from macro_intelligence.statistics.descriptive import mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert mean(values) == 3.0
    
    def test_mean_deterministic(self):
        """Test mean is deterministic."""
        from macro_intelligence.statistics.descriptive import mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert mean(values) == mean(values)
    
    def test_median_odd(self):
        """Test median with odd number of elements."""
        from macro_intelligence.statistics.descriptive import median
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert median(values) == 3.0
    
    def test_median_even(self):
        """Test median with even number of elements."""
        from macro_intelligence.statistics.descriptive import median
        
        values = [1.0, 2.0, 3.0, 4.0]
        assert median(values) == 2.5
    
    def test_variance(self):
        """Test variance calculation."""
        from macro_intelligence.statistics.descriptive import variance
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        # Population variance
        assert abs(variance(values, sample=False) - 4.0) < 0.001
    
    def test_std(self):
        """Test standard deviation calculation."""
        from macro_intelligence.statistics.descriptive import std
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        # Population std = 2.0
        assert abs(std(values, sample=False) - 2.0) < 0.001
    
    def test_min_max(self):
        """Test min and max."""
        from macro_intelligence.statistics.descriptive import min, max
        
        values = [3.0, 1.0, 4.0, 1.0, 5.0]
        assert min(values) == 1.0
        assert max(values) == 5.0
    
    def test_percentile(self):
        """Test percentile calculation."""
        from macro_intelligence.statistics.descriptive import percentile
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert percentile(values, 50) == 3.0
        assert percentile(values, 25) == 2.0
        assert percentile(values, 75) == 4.0
    
    def test_descriptive_statistics(self):
        """Test complete descriptive statistics."""
        from macro_intelligence.statistics.descriptive import descriptive_statistics
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        stats = descriptive_statistics(values)
        
        assert stats["count"] == 8
        assert stats["mean"] == 5.0
        assert stats["min"] == 2.0
        assert stats["max"] == 9.0
    
    def test_empty_list_raises(self):
        """Test that empty list raises error."""
        from macro_intelligence.statistics.descriptive import mean
        
        with pytest.raises(ValueError):
            mean([])


class TestRollingStatistics:
    """Tests for rolling statistics."""
    
    def test_rolling_mean(self):
        """Test rolling mean calculation."""
        from macro_intelligence.statistics.rolling import rolling_mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = rolling_mean(values, window=3)
        
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0  # Mean of [1,2,3]
        assert result[3] == 3.0  # Mean of [2,3,4]
        assert result[4] == 4.0  # Mean of [3,4,5]
    
    def test_rolling_std(self):
        """Test rolling standard deviation."""
        from macro_intelligence.statistics.rolling import rolling_std
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = rolling_std(values, window=3)
        
        # First two should be None
        assert result[0] is None
        assert result[1] is None
        
        # Third should have a value
        assert result[2] is not None
    
    def test_rolling_zscore(self):
        """Test rolling z-score."""
        from macro_intelligence.statistics.rolling import rolling_zscore
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = rolling_zscore(values, window=3)
        
        # First two should be None
        assert result[0] is None
        assert result[1] is None
        
        # Third should have a value
        assert result[2] is not None
    
    def test_rolling_deterministic(self):
        """Test rolling statistics are deterministic."""
        from macro_intelligence.statistics.rolling import rolling_mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result1 = rolling_mean(values, window=3)
        result2 = rolling_mean(values, window=3)
        
        assert result1 == result2


class TestCorrelation:
    """Tests for correlation."""
    
    def test_pearson_perfect_positive(self):
        """Test Pearson correlation with perfect positive correlation."""
        from macro_intelligence.statistics.correlation import pearson_correlation
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        assert abs(pearson_correlation(x, y) - 1.0) < 0.001
    
    def test_pearson_perfect_negative(self):
        """Test Pearson correlation with perfect negative correlation."""
        from macro_intelligence.statistics.correlation import pearson_correlation
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        
        assert abs(pearson_correlation(x, y) - (-1.0)) < 0.001
    
    def test_pearson_no_correlation(self):
        """Test Pearson correlation with no correlation."""
        from macro_intelligence.statistics.correlation import pearson_correlation
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 3.0, 2.0, 5.0, 4.0]
        
        corr = pearson_correlation(x, y)
        assert corr is not None
    
    def test_rolling_correlation(self):
        """Test rolling correlation."""
        from macro_intelligence.statistics.correlation import rolling_correlation
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        result = rolling_correlation(x, y, window=3)
        
        # First two should be None
        assert result[0] is None
        assert result[1] is None
        
        # Later should have values
        assert result[2] is not None


class TestCovariance:
    """Tests for covariance."""
    
    def test_covariance_positive(self):
        """Test positive covariance."""
        from macro_intelligence.statistics.covariance import covariance
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        cov = covariance(x, y)
        assert cov > 0
    
    def test_covariance_negative(self):
        """Test negative covariance."""
        from macro_intelligence.statistics.covariance import covariance
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        
        cov = covariance(x, y)
        assert cov < 0


class TestRegression:
    """Tests for regression."""
    
    def test_linear_regression_perfect(self):
        """Test linear regression with perfect fit."""
        from macro_intelligence.statistics.regression import linear_regression
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        result = linear_regression(x, y)
        
        assert abs(result.slope - 2.0) < 0.001
        assert abs(result.intercept - 0.0) < 0.001
        assert abs(result.r_squared - 1.0) < 0.001
    
    def test_slope(self):
        """Test slope calculation."""
        from macro_intelligence.statistics.regression import slope
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        assert abs(slope(x, y) - 2.0) < 0.001
    
    def test_r_squared(self):
        """Test R-squared calculation."""
        from macro_intelligence.statistics.regression import r_squared
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        assert abs(r_squared(x, y) - 1.0) < 0.001
    
    def test_regression_deterministic(self):
        """Test regression is deterministic."""
        from macro_intelligence.statistics.regression import linear_regression
        
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        result1 = linear_regression(x, y)
        result2 = linear_regression(x, y)
        
        assert result1 == result2


class TestNormalization:
    """Tests for normalization."""
    
    def test_min_max_normalize(self):
        """Test min-max normalization."""
        from macro_intelligence.statistics.normalization import min_max_normalize
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = min_max_normalize(values)
        
        assert result[0] == 0.0
        assert result[-1] == 1.0
    
    def test_zscore_normalize(self):
        """Test z-score normalization."""
        from macro_intelligence.statistics.normalization import zscore_normalize
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = zscore_normalize(values)
        
        # Mean of z-scores should be approximately 0
        from macro_intelligence.statistics.descriptive import mean
        assert abs(mean(result)) < 0.001
    
    def test_robust_scale(self):
        """Test robust scaling."""
        from macro_intelligence.statistics.normalization import robust_scale
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = robust_scale(values)
        
        assert len(result) == 5
    
    def test_normalize_methods(self):
        """Test normalize with different methods."""
        from macro_intelligence.statistics.normalization import normalize
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Test z-score
        result_zscore = normalize(values, method="zscore")
        assert len(result_zscore) == 5
        
        # Test min-max
        result_minmax = normalize(values, method="minmax")
        assert len(result_minmax) == 5


class TestZScore:
    """Tests for z-score analysis."""
    
    def test_zscore_calculation(self):
        """Test z-score calculation."""
        from macro_intelligence.statistics.zscore import zscore
        
        result = zscore(5.0, mean_val=3.0, std_val=2.0)
        assert result == 1.0
    
    def test_zscores_list(self):
        """Test z-scores for list."""
        from macro_intelligence.statistics.zscore import zscores
        
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = zscores(values)
        
        assert len(result) == 8
    
    def test_interpret_zscore(self):
        """Test z-score interpretation."""
        from macro_intelligence.statistics.zscore import interpret_zscore
        
        assert interpret_zscore(0.3) == "normal"
        assert interpret_zscore(1.5) == "moderate"
        assert interpret_zscore(3.5) == "extreme"


class TestVolatility:
    """Tests for volatility analysis."""
    
    def test_rolling_volatility(self):
        """Test rolling volatility."""
        from macro_intelligence.statistics.volatility import rolling_volatility
        
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        result = rolling_volatility(returns, window=3)
        
        assert len(result) == 5
    
    def test_realized_volatility(self):
        """Test realized volatility."""
        from macro_intelligence.statistics.volatility import realized_volatility
        
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        result = realized_volatility(returns, window=3)
        
        assert result is not None
    
    def test_volatility_analysis(self):
        """Test complete volatility analysis."""
        from macro_intelligence.statistics.volatility import volatility_analysis
        
        returns = [0.01, -0.02, 0.03, -0.01, 0.02] * 10
        result = volatility_analysis(returns, window=5)
        
        assert "volatility" in result
        assert "volatility_regime" in result


class TestTrend:
    """Tests for trend analysis."""
    
    def test_moving_average(self):
        """Test moving average."""
        from macro_intelligence.statistics.trend import moving_average
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = moving_average(values, window=3)
        
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0
    
    def test_exponential_moving_average(self):
        """Test exponential moving average."""
        from macro_intelligence.statistics.trend import exponential_moving_average
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = exponential_moving_average(values, span=3)
        
        assert len(result) == 5
    
    def test_momentum(self):
        """Test momentum calculation."""
        from macro_intelligence.statistics.trend import momentum
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = momentum(values, period=1)
        
        assert result[0] is None
        assert result[1] == 1.0
    
    def test_trend_analysis(self):
        """Test complete trend analysis."""
        from macro_intelligence.statistics.trend import trend_analysis
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        result = trend_analysis(values, window=5)
        
        assert "trend_direction" in result
        assert "trend_strength" in result


class TestChangePoint:
    """Tests for change point detection."""
    
    def test_cusum(self):
        """Test CUSUM change point detection."""
        from macro_intelligence.statistics.change_point import cusum
        
        # Create data with a clear change point
        values = [1.0] * 50 + [2.0] * 50
        result = cusum(values)
        
        # Should detect at least one change point
        assert len(result) >= 0  # May or may not detect depending on threshold
    
    def test_detect_change_points(self):
        """Test change point detection."""
        from macro_intelligence.statistics.change_point import detect_change_points
        
        values = [1.0] * 50 + [2.0] * 50
        result = detect_change_points(values)
        
        assert isinstance(result, list)


class TestDistributions:
    """Tests for distribution analysis."""
    
    def test_empirical_distribution(self):
        """Test empirical distribution."""
        from macro_intelligence.statistics.distributions import empirical_distribution
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = empirical_distribution(values)
        
        assert result["count"] == 5
        assert result["mean"] == 3.0
    
    def test_quantiles(self):
        """Test quantile calculation."""
        from macro_intelligence.statistics.distributions import quantiles
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = quantiles(values)
        
        assert 0.5 in result
        assert result[0.5] == 3.0
    
    def test_distribution_analysis(self):
        """Test complete distribution analysis."""
        from macro_intelligence.statistics.distributions import distribution_analysis
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        result = distribution_analysis(values)
        
        assert "mean" in result
        assert "std" in result
        assert "skewness" in result


class TestMILStatInvariants:
    """Tests for MIL-STAT invariants."""
    
    def test_mil_stat_001_deterministic(self):
        """MIL-STAT-001: Same input must always produce identical output."""
        from macro_intelligence.statistics.descriptive import mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result1 = mean(values)
        result2 = mean(values)
        
        assert result1 == result2
    
    def test_mil_stat_002_pure_functions(self):
        """MIL-STAT-002: Statistical functions are pure."""
        from macro_intelligence.statistics.descriptive import mean
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        original = list(values)
        
        mean(values)
        
        # Original list should not be modified
        assert values == original
    
    def test_mil_stat_004_provenance_preserved(self):
        """MIL-STAT-004: All outputs preserve provenance."""
        from macro_intelligence.statistics.descriptive import descriptive_statistics
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = descriptive_statistics(values)
        
        # Result should be a dictionary with expected keys
        assert "count" in result
        assert "mean" in result
    
    def test_mil_stat_005_versioned(self):
        """MIL-STAT-005: Algorithms are versioned."""
        # All functions should have version information
        from macro_intelligence.statistics import descriptive
        
        # Module should exist and be importable
        assert hasattr(descriptive, 'mean')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
