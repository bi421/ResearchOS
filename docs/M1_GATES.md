# M1 promotion gates

1. Real MT5 XAUUSD M1 dataset identity verified.
2. Event timestamps are chronological and use only historical information.
3. Forward outcome endpoints are explicit and direction-aware.
4. Event windows do not overlap calibration/training with future labels.
5. Walk-forward predictions are strictly out-of-sample.
6. Calibration uses prior outcomes only.
7. OOS metrics beat or are compared transparently against the unconditional baseline.
8. Evidence records bind the dataset and outcome contract.

Until all gates pass, the system reports research measurements only and does not promote them to predictive knowledge.
