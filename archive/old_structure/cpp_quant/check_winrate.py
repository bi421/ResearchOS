import sys

sys.path.insert(0, "python")
sys.path.insert(0, "build/Release")
import glob

import pandas as pd
from cpp_quant import CppQuant

df = pd.concat(
    [
        pd.read_csv(
            f,
            sep=";",
            header=None,
            names=["datetime", "open", "high", "low", "close", "volume"],
            dtype={"datetime": str},
        )
        .assign(datetime=lambda x: pd.to_datetime(x["datetime"], format="%Y%m%d %H%M%S"))
        .dropna(subset=["datetime"])
        .set_index("datetime")
        for f in glob.glob("../data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
    ]
).sort_index()

df_d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
print("1D Candle:", len(df_d))

engine = CppQuant()
engine.load_from_dataframe(df_d)
result = engine.run_sma(20, 50)

print("???? ???????:", result["num_trades"])
print("Winrate:", round(result["winrate"], 4), "%")
print("???? ?????:", round(result["total_return"], 4), "%")
