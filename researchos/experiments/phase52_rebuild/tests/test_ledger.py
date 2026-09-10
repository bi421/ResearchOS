from pathlib import Path

from researchos.experiments.phase52_rebuild.ledger import LedgerConfig, build_data_ledger


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_four_way_intersection_and_loss_ledger(tmp_path: Path) -> None:
    xau = tmp_path / "xau.csv"
    dxy = tmp_path / "dxy.csv"
    us10y = tmp_path / "us10y.csv"
    vix = tmp_path / "vix.csv"
    _write(xau, "Date,Time,Open,High,Low,Close,Volume\n" + "\n".join(
        f"2021.01.{i:02d},00:00,1,2,0,1,10" for i in range(4, 15)
    ) + "\n")
    _write(dxy, "timestamp,open,high,low,close,volume\n" + "\n".join(
        f"{1609718400000 + (i-4)*86400000},1,2,0,1,1" for i in range(4, 14)
    ) + "\n")
    _write(us10y, "observation_date,DGS10\n" + "\n".join(
        f"2021-01-{i:02d},1.0" for i in range(4, 15)
    ) + "\n")
    _write(vix, "observation_date,VIXCLS\n" + "\n".join(
        f"2021-01-{i:02d},20.0" for i in range(4, 15)
    ) + "\n")

    ledger = build_data_ledger(xau, dxy, us10y, vix, LedgerConfig(feature_warmup=2, label_horizon=2))
    assert ledger.common_rows == 10
    assert ledger.xau_minus_common == 1
    assert ledger.feature_warmup_rows == 2
    assert ledger.after_feature_warmup == 8
    assert ledger.label_horizon_rows == 2
    assert ledger.final_usable_rows == 6
    assert ledger.invariant_ok


def test_fred_missing_value_is_excluded_not_synthesized(tmp_path: Path) -> None:
    files = [tmp_path / n for n in ("xau.csv", "dxy.csv", "us10y.csv", "vix.csv")]
    _write(files[0], "Date,Time,Open,High,Low,Close,Volume\n2021.01.04,00:00,1,2,0,1,10\n2021.01.05,00:00,1,2,0,1,10\n")
    _write(files[1], "timestamp,open,high,low,close,volume\n1609718400000,1,2,0,1,1\n1609804800000,1,2,0,1,1\n")
    _write(files[2], "observation_date,DGS10\n2021-01-04,1.0\n2021-01-05,.\n")
    _write(files[3], "observation_date,VIXCLS\n2021-01-04,20.0\n2021-01-05,20.0\n")
    ledger = build_data_ledger(*files, LedgerConfig(feature_warmup=0, label_horizon=0))
    assert ledger.common_rows == 1
    assert ledger.final_usable_rows == 1
    assert ledger.invariant_ok
