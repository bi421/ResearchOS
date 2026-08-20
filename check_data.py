import pandas as pd
import glob
files = glob.glob('data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv')
df = pd.concat([pd.read_csv(f, sep=';', header=None, names=['datetime','open','high','low','close','volume']) for f in files], ignore_index=True)
df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
print(f'Total rows: {len(df)}')
print(f'Latest date: {df["datetime"].max()}')
print(f'2026 rows: {df[df["datetime"].dt.year == 2026].shape[0]}')
