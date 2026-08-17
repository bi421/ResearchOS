"""
ResearchOS Macro Intelligence Layer - Series Registry
"""

from __future__ import annotations

from typing import Any

from macro_intelligence.contracts.enums import FrequencyEnum

# Supported series registry
SUPPORTED_SERIES: dict[str, dict[str, Any]] = {
    # Dollar Index
    "DXY": {
        "name": "US Dollar Index",
        "frequency": FrequencyEnum.DAILY,
        "unit": "index",
        "source": "ICE",
        "range": (80.0, 160.0),
    },
    # Treasury Yields
    "US2Y": {
        "name": "US Treasury 2-Year Yield",
        "frequency": FrequencyEnum.DAILY,
        "unit": "percent",
        "source": "FRED/Treasury",
        "range": (-5.0, 20.0),
    },
    "US5Y": {
        "name": "US Treasury 5-Year Yield",
        "frequency": FrequencyEnum.DAILY,
        "unit": "percent",
        "source": "FRED/Treasury",
        "range": (-5.0, 20.0),
    },
    "US10Y": {
        "name": "US Treasury 10-Year Yield",
        "frequency": FrequencyEnum.DAILY,
        "unit": "percent",
        "source": "FRED/Treasury",
        "range": (-5.0, 20.0),
    },
    "US30Y": {
        "name": "US Treasury 30-Year Yield",
        "frequency": FrequencyEnum.DAILY,
        "unit": "percent",
        "source": "FRED/Treasury",
        "range": (-5.0, 20.0),
    },
    # Real Yields
    "REAL_10Y": {
        "name": "10-Year Real Yield (Nominal - Breakeven)",
        "frequency": FrequencyEnum.DAILY,
        "unit": "percent",
        "source": "FRED (computed)",
        "computed_from": ["US10Y", "T10YIE"],
        "range": (-10.0, 15.0),
    },
    # Inflation
    "CPI_YOY": {
        "name": "CPI Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (-10.0, 50.0),
    },
    "CPI_CORE_YOY": {
        "name": "Core CPI Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (-5.0, 40.0),
    },
    "CPI_MOM": {
        "name": "CPI Month-over-Month",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (-10.0, 20.0),
    },
    "PPI_YOY": {
        "name": "PPI Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (-10.0, 50.0),
    },
    "PPI_CORE_YOY": {
        "name": "Core PPI Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (-10.0, 50.0),
    },
    "PCE_YOY": {
        "name": "PCE Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BEA/FRED",
        "range": (-10.0, 50.0),
    },
    "PCE_CORE_YOY": {
        "name": "Core PCE Year-over-Year",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BEA/FRED",
        "range": (-10.0, 50.0),
    },
    # Labor
    "NFP_CHANGE": {
        "name": "Non-Farm Payrolls Change",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "thousands",
        "source": "BLS",
        "range": (-200.0, 1000.0),
    },
    "UNRATE": {
        "name": "Unemployment Rate",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "percent",
        "source": "BLS/FRED",
        "range": (0.0, 50.0),
    },
    "JOLTS_TOTAL": {
        "name": "JOLTS Total Job Openings",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "thousands",
        "source": "BLS",
        "range": (0.0, 12000.0),
    },
    "JOLTS_HIRINGS": {
        "name": "JOLTS Hires",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "thousands",
        "source": "BLS",
        "range": (0.0, 10000.0),
    },
    "JOLTS_SEPARATIONS": {
        "name": "JOLTS Separations",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "thousands",
        "source": "BLS",
        "range": (0.0, 10000.0),
    },
    # GDP
    "GDP_YOY": {
        "name": "GDP Year-over-Year",
        "frequency": FrequencyEnum.QUARTERLY,
        "unit": "percent",
        "source": "BEA/FRED",
        "range": (-20.0, 30.0),
    },
    "GDP_MOM": {
        "name": "GDP Month-over-Month (Annualized)",
        "frequency": FrequencyEnum.QUARTERLY,
        "unit": "percent_ann",
        "source": "BEA/FRED",
        "range": (-20.0, 30.0),
    },
    # PMI
    "PMI_MFG": {
        "name": "ISM Manufacturing PMI",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "index",
        "source": "ISM",
        "range": (20.0, 80.0),
    },
    "PMI_SVC": {
        "name": "ISM Services PMI",
        "frequency": FrequencyEnum.MONTHLY,
        "unit": "index",
        "source": "ISM",
        "range": (20.0, 80.0),
    },
    # Volatility
    "VIX": {
        "name": "CBOE Volatility Index",
        "frequency": FrequencyEnum.DAILY,
        "unit": "index",
        "source": "CBOE",
        "range": (10.0, 200.0),
    },
    "MOVE": {
        "name": "ICE BofAMOVE Index",
        "frequency": FrequencyEnum.DAILY,
        "unit": "index",
        "source": "Goldman Sachs",
        "range": (50.0, 500.0),
    },
}


# Validation ranges for range validator
SERIES_RANGES: dict[str, tuple[float, float]] = {
    series: info["range"] for series, info in SUPPORTED_SERIES.items()
}


def get_series_metadata(series_id: str) -> dict | None:
    """Get metadata for a series."""
    return SUPPORTED_SERIES.get(series_id)


def is_supported_series(series_id: str) -> bool:
    """Check if series is supported."""
    return series_id in SUPPORTED_SERIES


def get_all_series_ids() -> list[str]:
    """Get all supported series IDs."""
    return list(SUPPORTED_SERIES.keys())
