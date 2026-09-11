from researchos.experiments.phase52_rebuild.warmup_audit import audit_warmup_coverage


def test_warmup_requires_prior_common_days():
    result = audit_warmup_coverage(
        xau_days={"2021-01-01", "2021-01-04", "2021-01-05"},
        dxy_days={"2021-01-01", "2021-01-04", "2021-01-05"},
        us10y_days={"2021-01-01", "2021-01-04", "2021-01-05"},
        vix_days={"2021-01-01", "2021-01-04", "2021-01-05"},
        research_start_day="2021-01-04",
        warmup_rows_required=1,
    )
    assert result.common_days_before_research == 1
    assert result.required_context_start_day == "2021-01-01"
    assert result.context_available is True
    assert result.status == "PASS"


def test_current_style_source_without_preperiod_is_blocked():
    result = audit_warmup_coverage(
        xau_days={"2021-01-04", "2021-01-05"},
        dxy_days={"2021-01-04", "2021-01-05"},
        us10y_days={"2021-01-04", "2021-01-05"},
        vix_days={"2021-01-04", "2021-01-05"},
        research_start_day="2021-01-04",
        warmup_rows_required=60,
    )
    assert result.common_days_before_research == 0
    assert result.required_context_start_day is None
    assert result.context_available is False
    assert result.status == "BLOCKED"
