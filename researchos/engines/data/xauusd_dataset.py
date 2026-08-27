from dataclasses import dataclass
from pathlib import Path

import polars as pl


# Ð­Ð½Ñ Ð±Ð¾Ð» Ñ‚Ð°Ð½Ñ‹ researchos/data_engine/dataset.py Ð´ÑÑÑ€ Ð½ÑÐ¼ÑÑ… Ñ‘ÑÑ‚Ð¾Ð¹ ÐºÐ»Ð°ÑÑ
@dataclass
class XAUUSD_M1_Dataset:
    path: Path = Path("data/curated/xauusd/xauusd_m1_2023_2025.parquet")

    def load(self, year=None, resample="1h"):
        df = pl.read_parquet(self.path).sort("ts_utc")
        if year:
            df = df.filter(pl.col("ts_utc").dt.year() == year)
        if resample:
            df = (
                df.group_by_dynamic("ts_utc", every=resample)
                .agg(
                    [
                        pl.col("open").first().alias("open"),
                        pl.col("high").max().alias("high"),
                        pl.col("low").min().alias("low"),
                        pl.col("close").last().alias("close"),
                    ]
                )
                .sort("ts_utc")
            )
        return df


# Ð¢ÐµÑÑ‚
if __name__ == "__main__":
    ds = XAUUSD_M1_Dataset()
    print("H1 2025:", ds.load(year=2025, resample="1h").height, "rows")
    print("M1 2025:", ds.load(year=2025, resample=None).height, "rows")
    print("Ð‘ÑÐ»ÑÐ½ - Ð¾Ð´Ð¾Ð¾ Ñ‚Ð°Ð½Ñ‹ Ð±Ò¯Ñ… experiment Ò¯Ò¯Ð½Ð¸Ð¹Ð³ Ð´ÑƒÑƒÐ´Ð°Ð¶ Ð±Ð¾Ð»Ð½Ð¾: XAUUSD_M1_Dataset().load()")
