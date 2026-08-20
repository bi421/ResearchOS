import yfinance as yf
import pandas as pd
def fetch_multi_asset(symbols, start='2021-01-01', end='2026-08-20'):
    data = {}
    for sym in symbols:
        df = yf.download(sym, start=start, end=end, progress=False)
        data[sym] = df['Close']
    return pd.DataFrame(data).dropna()
# Жишээ ашиглалт: df = fetch_multi_asset(['GC=F','BTC-USD','EURUSD=X','^GSPC'])
