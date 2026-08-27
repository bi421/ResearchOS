import time

import polars as pl

f = "data/xauusd_1min.parquet"

t0 = time.time()
df_pl = pl.read_parquet(f)
print(f"Polars: {time.time()-t0:.3f}s, shape={df_pl.shape}")

# Pandas руу хөрвүүлэх хурд
t0 = time.time()
df_pd = df_pl.to_pandas()
print(f"To pandas: {time.time()-t0:.3f}s")
