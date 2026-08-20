import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_macro_data(start_date, end_date):
    symbols = ['DX-Y.NYB', '^VIX']
    data = {}
    for sym in symbols:
        try:
            df = yf.download(sym, start=start_date, end=end_date, progress=False)
            data[sym] = df['Close'].rename(sym.replace('-','').replace('^',''))
        except:
            pass
    if not data:
        return None
    macro_df = pd.DataFrame(data)
    macro_df.columns = ['dxy', 'vix']
    return macro_df

def merge_macro(df, macro_df):
    if macro_df is None or macro_df.empty: return df
    df = df.copy()
    macro_df = macro_df.reindex(df.index, method='ffill').fillna(method='ffill')
    df['dxy'] = macro_df['dxy'].values if 'dxy' in macro_df else 0
    df['vix'] = macro_df['vix'].values if 'vix' in macro_df else 0
    df['dxy_return'] = df['dxy'].pct_change()
    df['vix_return'] = df['vix'].pct_change()
    return df
