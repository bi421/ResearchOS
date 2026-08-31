import re


def check_result(result, source_code_path=None):
    findings = []

    def flag(level, msg):
        findings.append((level, msg))

    if source_code_path:
        try:
            with open(source_code_path, "r", encoding="utf-8") as f:
                code = f.read()
            danger_words = ["synthetic", "generate_xauusd_synthetic", "np.random", "fake_data", "dummy_data"]
            hits = [w for w in danger_words if re.search(w, code, re.IGNORECASE)]
            if hits:
                flag("FAIL", "Source code contains synthetic-data markers: " + str(hits) + ". Verify this isn't the code path actually executed.")
            else:
                flag("PASS", "No synthetic-data markers found in source.")
        except FileNotFoundError:
            flag("WARN", "Could not read " + source_code_path + " to check for synthetic data.")

    if "sharpe_ratio" in result:
        sr = result["sharpe_ratio"]
        if sr > 3.0:
            flag("FAIL", "Sharpe ratio " + str(round(sr, 2)) + " is implausibly high for a real " "daily/hourly strategy (top hedge funds run 2-3). " "Strongly suspect synthetic data or calculation bug.")
        else:
            flag("PASS", "Sharpe ratio " + str(round(sr, 2)) + " is in a plausible range.")

    if "profit_factor" in result:
        pf = result["profit_factor"]
        if pf == float("inf") or (isinstance(pf, float) and pf > 10):
            flag("FAIL", "Profit factor " + str(pf) + " is implausible (infinite or >10 " "means zero/near-zero losing trades - check for a " "labeling or data bug).")
        else:
            flag("PASS", "Profit factor " + str(pf) + " is in a plausible range.")

    if "model_acc" in result and "target_type" in result:
        acc = result["model_acc"]
        if result["target_type"] == "binary" and (acc < 0.40 or acc > 0.75):
            flag("WARN", "Binary accuracy " + str(round(acc, 4)) + " is far from 50% in either " "direction. If far BELOW 50%, suspect an inverted " "label or category-mismatch bug (see Check 3) before " "trusting this as a real negative result.")
        else:
            flag("PASS", "Accuracy " + str(round(acc, 4)) + " is in a plausible range for binary " "direction prediction.")

    if "signal_type" in result and "target_type" in result:
        if result["signal_type"] != result["target_type"]:
            flag("FAIL", "Signal type (" + result["signal_type"] + ") does not match " "target type (" + result["target_type"] + "). This is EXACTLY " "the bug that made LightGBM show 35.59% instead of the " "real 52.94% today. Verify how the mismatch is handled " "before trusting any accuracy number.")
        else:
            flag("PASS", "Signal type matches target type.")

    if "p_value" in result and "n_hypotheses_tested" in result:
        n_tests = result["n_hypotheses_tested"]
        p = result["p_value"]
        if n_tests > 1:
            corrected_alpha = 0.05 / n_tests
            if p < 0.05 and p >= corrected_alpha:
                flag("FAIL", "p=" + str(round(p, 4)) + " passes uncorrected alpha=0.05 but FAILS " "Bonferroni-corrected alpha=" + str(round(corrected_alpha, 4)) + " (" + str(n_tests) + " hypotheses tested). This is exactly the " "20-day-horizon false positive from today. Do not " "treat this as significant.")
            elif p < corrected_alpha:
                flag("WARN", "p=" + str(round(p, 4)) + " passes Bonferroni correction " "(alpha=" + str(round(corrected_alpha, 4)) + ") - but still confirm " "this survives a true holdout test (Check 5) before " "trusting it.")
            else:
                flag("PASS", "p=" + str(round(p, 4)) + " does not pass even the uncorrected " "threshold - consistent null result.")
        else:
            flag("WARN", "Only 1 hypothesis reported as tested - if more were " "actually tried and not reported, this p-value is " "meaningless (undisclosed multiple testing).")

    if "n" in result and "horizon_days" in result and "total_days_in_dataset" in result:
        max_non_overlapping = result["total_days_in_dataset"] // result["horizon_days"]
        if result["n"] > max_non_overlapping * 1.5:
            flag("FAIL", "N=" + str(result["n"]) + " is much larger than the max possible " "non-overlapping sample size (~" + str(max_non_overlapping) + ") for a " + str(result["horizon_days"]) + "-day horizon. This " "suggests overlapping windows inflating N and shrinking " "p-values artificially - exactly today's 20-day false " "positive (N=981 overlapping vs N=50 non-overlapping).")
        else:
            flag("PASS", "Sample size is consistent with non-overlapping windows.")

    if "holdout_start_date" in result and "train_end_date" in result:
        if result["train_end_date"] >= result["holdout_start_date"]:
            flag("FAIL", "Training data extends to " + str(result["train_end_date"]) + ", which is at or after the holdout start " "(" + str(result["holdout_start_date"]) + "). Holdout is " "contaminated - the result is not a true out-of-sample test.")
        else:
            flag("PASS", "Training period ends strictly before holdout start.")

    return findings


def print_report(findings):
    print("=" * 70)
    print("OUTPUT VERIFICATION REPORT")
    print("=" * 70)
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    passes = [f for f in findings if f[0] == "PASS"]

    for level, msg in findings:
        marker = {"FAIL": "[FAIL]", "WARN": "[WARN]", "PASS": "[PASS]"}[level]
        print(marker + " " + msg)

    print("-" * 70)
    print("Summary: " + str(len(passes)) + " passed, " + str(len(warns)) + " warnings, " + str(len(fails)) + " FAILED")
    if fails:
        print("")
        print(">>> DO NOT TRUST this result until FAILED checks are resolved. <<<")
    elif warns:
        print("")
        print(">>> Result is plausible but review warnings before trusting fully. <<<")
    else:
        print("")
        print(">>> No red flags found by this checker. Still not a guarantee of")
        print("    a real edge - this only catches known failure patterns. <<<")
    print("=" * 70)


if __name__ == "__main__":
    example_result = {
        "n": 981,
        "horizon_days": 20,
        "total_days_in_dataset": 1253,
        "model_acc": 0.6718,
        "baseline_acc": 0.6422,
        "p_value": 0.0283,
        "n_hypotheses_tested": 4,
        "target_type": "binary",
        "signal_type": "binary",
        "sharpe_ratio": 1.2,
        "profit_factor": 1.8,
    }
    findings = check_result(example_result)
    print_report(findings)
