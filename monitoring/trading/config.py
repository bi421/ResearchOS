import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency for local development
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


def _get_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}. Set it in your shell or a local .env file before starting the trading bot.")
    return value


EXCHANGE = {
    "name": "binance",
    "apiKey": os.getenv("BINANCE_API_KEY", ""),
    "secret": os.getenv("BINANCE_API_SECRET", ""),
    "enableRateLimit": True,
    "options": {"defaultType": "spot"},
}

# Fail fast if credentials are not configured, instead of shipping a real secret in source.
if not EXCHANGE["apiKey"]:
    EXCHANGE["apiKey"] = _get_env("BINANCE_API_KEY")
if not EXCHANGE["secret"]:
    EXCHANGE["secret"] = _get_env("BINANCE_API_SECRET")

STRATEGY = {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "fast_ma": 5,
    "slow_ma": 20,
    "trend_ma": 200,
    "atr_period": 14,
    "atr_multiplier": 2.0,
}
RISK = {"max_position_size": 0.01}
