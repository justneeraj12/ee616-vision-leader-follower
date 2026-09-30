import json
import math

from ee616_evaluation.summarize_timing_gate import summarize
from ee616_evaluation.timing_gate_evaluator import latency_summary, stamped_rate_hz


def test_latency_summary_reports_percentiles():
    result = latency_summary([1.0, 2.0, 3.0, 4.0])
    assert result["count"] == 4
    assert result["p50_ms"] == 2.5
    assert result["p95_ms"] > result["p50_ms"]
    assert result["max_ms"] == 4.0


def test_stamped_rate_uses_unique_message_stamps():
    assert math.isclose(stamped_rate_hz([1.0, 1.0, 1.1, 1.2]), 10.0)
    assert stamped_rate_hz([1.0]) is None


def _timing_run(repetition):
    latency = {
        stage: {"count": 10, "p95_ms": 20.0, "p99_ms": 22.0, "max_ms": 25.0}
        for stage in (
            "camera_to_measurement", "measurement_to_controller_cmd",
            "controller_to_actual_cmd", "detector_inference", "control_period",
        )
    }
    follower = {
        "camera_rate_hz": 15.0,
        "measurement_rate_hz": 15.0,
        "measurement_delivery_ratio": 1.0,
        "latency": latency,
    }
    return {
        "run_id": f"run_{repetition:02d}",
        "status": "pass",
        "real_time_factor": 1.0,
        "followers": {str(index): follower for index in range(1, 4)},
    }


def test_timing_summary_requires_timing_behavior_and_resources(tmp_path):
    for repetition in range(1, 4):
        timing = _timing_run(repetition)
        (tmp_path / f"timing_3_combined_run_{repetition:02d}_summary.json").write_text(
            json.dumps(timing), encoding="utf-8"
        )
        behavior = {"status": "pass"}
        (tmp_path / f"disturbance_3_combined_run_{repetition:02d}_summary.json").write_text(
            json.dumps(behavior), encoding="utf-8"
        )
    (tmp_path / "resources.json").write_text(json.dumps({
        "peak_gpu_memory_mib": 700.0,
        "peak_memory_mib": 3500.0,
    }), encoding="utf-8")
    (tmp_path / "resource_samples.csv").write_text("elapsed_s\n0.0\n", encoding="utf-8")
    result = summarize(tmp_path)
    assert result["status"] == "pass"
    assert result["run_count"] == 3
