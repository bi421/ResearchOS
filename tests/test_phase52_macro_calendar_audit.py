from __future__ import annotations

import csv
from pathlib import Path

from scripts.audit_phase52_macro_calendar import audit


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_canonical_audit_uses_observation_values_and_exact_intersection(tmp_path: Path) -> None:
    xau = tmp_path / "xau.csv"
    dxy = tmp_path / "dxy.csv"
    dgs10 = tmp_path / "dgs10.csv"
    vix = tmp_path / "vix.csv"

    write_csv(
        xau,
        ["Date", "Time", "Open", "High", "Low", "Close", "Volume"],
        [
            {"Date": "2021.01.04", "Time": "00:00", "Open": 1, "High": 2, "Low": 1, "Close": 2, "Volume": 1},
            {"Date": "2021.01.05", "Time": "00:00", "Open": 1, "High": 2, "Low": 1, "Close": 2, "Volume": 1},
            {"Date": "2021.01.06", "Time": "00:00", "Open": 1, "High": 2, "Low": 1, "Close": 2, "Volume": 1},
        ],
    )
    write_csv(
        dxy,
        ["timestamp", "open", "high", "low", "close", "volume"],
        [
            {"timestamp": 1609718400000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"timestamp": 1609804800000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"timestamp": 1609891200000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"timestamp": 1609977600000, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        ],
    )
    write_csv(
        dgs10,
        ["DATE", "DGS10"],
        [
            {"DATE": "2021-01-04", "DGS10": "0.93"},
            {"DATE": "2021-01-05", "DGS10": "0.95"},
            {"DATE": "2021-01-06", "DGS10": "."},
        ],
    )
    write_csv(
        vix,
        ["observation_date", "VIXCLS"],
        [
            {"observation_date": "2021-01-04", "VIXCLS": "24.08"},
            {"observation_date": "2021-01-05", "VIXCLS": "25.34"},
            {"observation_date": "2021-01-06", "VIXCLS": "25.07"},
        ],
    )

    result = audit(xau, dxy, dgs10, vix)
    intersection = result["intersection"]

    assert intersection["xauusd"] == 3
    assert intersection["xauusd_dxy"] == 3
    assert intersection["xauusd_dgs10"] == 2
    assert intersection["xauusd_vix"] == 3
    assert intersection["four_way"] == 2
    assert intersection["xauusd_dropped"] == 1
    assert intersection["xauusd_only"] == ["2021-01-06"]
    assert intersection["dxy_only"] == ["2021-01-07"]
    assert result["sources"]["DGS10"]["missing_value_rows"] == 1


def test_dxy_identity_is_explicitly_secondary(tmp_path: Path) -> None:
    paths = [tmp_path / name for name in ("xau.csv", "dxy.csv", "dgs10.csv", "vix.csv")]
    write_csv(paths[0], ["Date"], [{"Date": "2021.01.04"}])
    write_csv(paths[1], ["timestamp"], [{"timestamp": 1609718400000}])
    write_csv(paths[2], ["DATE", "DGS10"], [{"DATE": "2021-01-04", "DGS10": "0.93"}])
    write_csv(paths[3], ["DATE", "VIXCLS"], [{"DATE": "2021-01-04", "VIXCLS": "24.08"}])

    result = audit(*paths)
    dxy = result["sources"]["DXY"]
    assert dxy["source"] == "Dukascopy"
    assert dxy["instrument"] == "dollaridxusd"
    assert dxy["source_type"] == "secondary"
    assert dxy["ice_equivalence"] == "NOT_PROVEN"
