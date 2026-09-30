"""Metric calculations for the camera-measurement gate."""

from __future__ import annotations

from math import ceil, sqrt
from typing import Any


RANGE_RMSE_LIMIT_M = 0.15
BEARING_MAE_LIMIT_DEG = 1.5
VALID_RATE_LIMIT = 0.95
LATENCY_P95_LIMIT_MS = 66.7


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    require_latency: bool = False,
) -> dict[str, Any]:
    """Summarize full-visibility rows using the approved gate thresholds."""
    full = [row for row in rows if bool(row["full_visibility"])]
    valid = [row for row in full if bool(row["valid"])]
    range_errors = [float(row["range_error_m"]) for row in valid]
    bearing_errors = [float(row["bearing_error_deg"]) for row in valid]
    valid_rate = len(valid) / len(full) if full else 0.0
    range_rmse = (
        sqrt(sum(value * value for value in range_errors) / len(range_errors))
        if range_errors
        else None
    )
    bearing_mae = (
        sum(abs(value) for value in bearing_errors) / len(bearing_errors)
        if bearing_errors
        else None
    )
    latencies = sorted(
        float(row["inference_ms"])
        for row in rows
        if row.get("inference_ms") is not None
    )
    latency_p95 = (
        latencies[max(0, ceil(0.95 * len(latencies)) - 1)]
        if latencies
        else None
    )
    latency_passed = (
        not require_latency
        or (
            len(latencies) == len(rows)
            and latency_p95 is not None
            and latency_p95 <= LATENCY_P95_LIMIT_MS
        )
    )
    finite = range_rmse is not None and bearing_mae is not None
    passed = (
        finite
        and valid_rate >= VALID_RATE_LIMIT
        and range_rmse <= RANGE_RMSE_LIMIT_M
        and bearing_mae <= BEARING_MAE_LIMIT_DEG
        and latency_passed
    )
    return {
        "status": "pass" if passed else "fail",
        "all_sample_count": len(rows),
        "full_visibility_sample_count": len(full),
        "valid_full_visibility_sample_count": len(valid),
        "valid_full_visibility_rate": valid_rate,
        "range_rmse_m": range_rmse,
        "bearing_mae_deg": bearing_mae,
        "inference_latency_sample_count": len(latencies),
        "inference_latency_p95_ms": latency_p95,
        "latency_required": require_latency,
        "thresholds": {
            "valid_full_visibility_rate_min": VALID_RATE_LIMIT,
            "range_rmse_m_max": RANGE_RMSE_LIMIT_M,
            "bearing_mae_deg_max": BEARING_MAE_LIMIT_DEG,
            "inference_latency_p95_ms_max": LATENCY_P95_LIMIT_MS,
        },
        "scope": (
            "camera-only fixed-red-target baseline in Gazebo; not YOLO, "
            "closed-loop control, physical-robot, or safety evidence"
        ),
    }
