from ee616_evaluation.metrics import summarize_rows


def _row(
    range_error,
    bearing_error,
    valid=True,
    full=True,
    inference_ms=None,
):
    return {
        "valid": valid,
        "full_visibility": full,
        "range_error_m": range_error,
        "bearing_error_deg": bearing_error,
        "inference_ms": inference_ms,
    }


def test_approved_thresholds_pass_good_measurements():
    rows = [_row(0.05, 0.5) for _ in range(100)]
    summary = summarize_rows(rows)
    assert summary["status"] == "pass"
    assert summary["valid_full_visibility_rate"] == 1.0
    assert summary["range_rmse_m"] == 0.05
    assert summary["bearing_mae_deg"] == 0.5


def test_invalid_rate_and_errors_fail_gate():
    rows = [_row(0.2, 2.0) for _ in range(94)]
    rows.extend(_row(None, None, valid=False) for _ in range(6))
    summary = summarize_rows(rows)
    assert summary["status"] == "fail"
    assert summary["valid_full_visibility_rate"] == 0.94


def test_cropped_rows_are_retained_but_not_scored():
    rows = [_row(0.01, 0.1), _row(10.0, 40.0, full=False)]
    summary = summarize_rows(rows)
    assert summary["all_sample_count"] == 2
    assert summary["full_visibility_sample_count"] == 1
    assert summary["status"] == "pass"


def test_required_latency_is_scored_at_p95():
    rows = [_row(0.05, 0.5, inference_ms=10.0) for _ in range(19)]
    rows.append(_row(0.05, 0.5, inference_ms=70.0))
    summary = summarize_rows(rows, require_latency=True)
    assert summary["inference_latency_p95_ms"] == 10.0
    assert summary["status"] == "pass"


def test_missing_required_latency_fails_gate():
    rows = [_row(0.05, 0.5, inference_ms=10.0) for _ in range(9)]
    rows.append(_row(0.05, 0.5))
    summary = summarize_rows(rows, require_latency=True)
    assert summary["status"] == "fail"


def test_detector_latency_includes_invalid_measurements():
    rows = [_row(0.05, 0.5, inference_ms=10.0)]
    rows.append(_row(None, None, valid=False, inference_ms=12.0))
    summary = summarize_rows(rows, require_latency=True)
    assert summary["inference_latency_sample_count"] == 2
    assert summary["inference_latency_p95_ms"] == 12.0
