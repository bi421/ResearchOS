from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import (
    build_daily_common_dataset,
    load_daily_xau_from_m1,
)


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_m1_is_aggregated_deterministically_by_utc_day(tmp_path: Path) -> None:
    xau = tmp_path / "xau.csv"
    _write(
        xau,
        "time,open,high,low,close,tick_volume,spread,real_volume\n"
        "2021-01-04T00:02:00Z,10,12,9,11,2,1,3\n"
        "2021-01-04T00:01:00Z,9,13,8,10,4,3,5\n"
        "2021-01-05T00:01:00Z,11,14,10,13,7,2,6\n",
    )
    bars = load_daily_xau_from_m1(xau)
    assert [b.day for b in bars] == ["2021-01-04", "2021-01-05"]
    first = bars[0]
    assert first.open == 9.0
    assert first.high == 13.0
    assert first.low == 8.0
    assert first.close == 11.0
    assert first.tick_volume == 6.0
    assert first.real_volume == 8.0
    assert first.spread == 2.0
    assert first.m1_rows == 2


def test_common_daily_dataset_never_fills_missing_macro_days(tmp_path: Path) -> None:
    xau = tmp_path / "xau.csv"
    dxy = tmp_path / "dxy.csv"
    us10y = tmp_path / "us10y.csv"
    vix = tmp_path / "vix.csv"
    _write(
        xau,
        "time,open,high,low,close,tick_volume,spread,real_volume\n"
        "2021-01-04T00:01:00Z,10,12,9,11,2,1,3\n"
        "2021-01-05T00:01:00Z,11,14,10,13,7,2,6\n"
        "2021-01-06T00:01:00Z,13,15,12,14,8,2,7\n",
    )
    _write(
        dxy,
        "timestamp,open,high,low,close,volume\n"
        "1609718400000,1,1,1,90,1\n"
        "1609804800000,1,1,1,91,1\n"
        "1609891200000,1,1,1,92,1\n",
    )
    _write(
        us10y,
        "observation_date,DGS10\n"
        "2021-01-04,1.1\n"
        "2021-01-05,.\n"
        "2021-01-06,1.3\n",
    )
    _write(
        vix,
        "observation_date,VIXCLS\n"
        "2021-01-04,20\n"
        "2021-01-05,21\n"
        "2021-01-06,22\n",
    )
    rows = build_daily_common_dataset(xau, dxy, us10y, vix)
    assert [r.day for r in rows] == ["2021-01-04", "2021-01-06"]
    assert [(r.dxy, r.us10y, r.vix) for r in rows] == [(90.0, 1.1, 20.0), (92.0, 1.3, 22.0)]


def test_daily_builder_is_deterministic(tmp_path: Path) -> None:
    xau = tmp_path / "xau.csv"
    dxy = tmp_path / "dxy.csv"
    us10y = tmp_path / "us10y.csv"
    vix = tmp_path / "vix.csv"
    _write(xau, "time,open,high,low,close,tick_volume,spread,real_volume\n2021-01-04T00:01:00Z,1,2,0,1.5,1,1,1\n")
    _write(dxy, "timestamp,open,high,low,close,volume\n1609718400000,1,1,1,90,1\n")
    _write(us10y, "observation_date,DGS10\n2021-01-04,1.1\n")
    _write(vix, "observation_date,VIXCLS\n2021-01-04,20\n")
    first = build_daily_common_dataset(xau, dxy, us10y, vix)
    second = build_daily_common_dataset(xau, dxy, us10y, vix)
    assert first == second
