import json
import subprocess

import pytest

from ee616_evaluation.disturbance_gate_evaluator import (
    _event_metrics,
    _read_with_retries,
    _stop_metrics,
    _stop_settled,
)
from ee616_evaluation.plot_disturbance_gate import _write_checksums
from ee616_evaluation.summarize_disturbance_gate import PAIR_SCENARIOS, summarize


def test_ground_truth_read_retries_a_transient_gazebo_failure():
    calls = 0

    def read_once():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise subprocess.CalledProcessError(1, ["gz", "topic"])
        return {"leader": "pose"}

    assert _read_with_retries(read_once, attempts=2) == {"leader": "pose"}
    assert calls == 2


def test_ground_truth_read_fails_after_bounded_attempts():
    def read_once():
        raise subprocess.TimeoutExpired(["gz", "topic"], 3.0)

    with pytest.raises(RuntimeError, match="after 2 attempts"):
        _read_with_retries(read_once, attempts=2)


def test_long_event_metrics_capture_predict_stop_and_recovery():
    rows = [
        {"elapsed_s": 9.0, "event": "LONG_OCCLUSION", "control_state": "TRACK", "linear_cmd_mps": 0.2, "angular_cmd_rps": 0.0, "spacing_error_m": 0.1},
        {"elapsed_s": 9.4, "event": "LONG_OCCLUSION", "control_state": "PREDICT", "linear_cmd_mps": 0.1, "angular_cmd_rps": 0.0, "spacing_error_m": 0.1},
        {"elapsed_s": 9.8, "event": "LONG_OCCLUSION", "control_state": "SAFE_STOP", "linear_cmd_mps": 0.0, "angular_cmd_rps": 0.0, "spacing_error_m": 0.1},
        {"elapsed_s": 10.4, "event": "NONE", "control_state": "TRACK", "linear_cmd_mps": 0.2, "angular_cmd_rps": 0.0, "spacing_error_m": 0.1},
    ]
    result = _event_metrics(rows, "LONG_OCCLUSION")
    assert result["predict_observed"]
    assert result["safe_stop_observed"]
    assert result["zero_command_during_safe_stop"]
    assert result["track_reacquisition_s"] <= 0.7


def test_stopped_leader_requires_settled_command_not_exact_gap():
    rows = [{
        "route_state": "STOPPED",
        "linear_cmd_mps": 0.0,
        "angular_cmd_rps": 0.0,
        "spacing_error_m": -0.14,
    }]
    assert _stop_settled(rows)
    assert _stop_metrics(rows)["final_spacing_error_m"] == -0.14


def test_stopped_leader_rejects_nonzero_command():
    rows = [{
        "route_state": "STOPPED",
        "linear_cmd_mps": 0.10,
        "angular_cmd_rps": 0.0,
        "spacing_error_m": 0.0,
    }]
    assert not _stop_settled(rows)


def test_checksum_manifest_covers_retained_evidence(tmp_path):
    for name, content in {
        "disturbance_1_long_occlusion_run_01_samples.csv": "rows\n",
        "disturbance_1_long_occlusion_run_01_summary.json": "{}\n",
        "pair_stage_summary.json": "{}\n",
        "resources.json": "{}\n",
        "summary.json": "{}\n",
        "disturbance_gate_metrics.png": "figure\n",
    }.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    manifest = _write_checksums(tmp_path).read_text(encoding="utf-8")
    assert "disturbance_1_long_occlusion_run_01_samples.csv" in manifest
    assert "summary.json" in manifest
    assert "SHA256SUMS" not in manifest


def _passing_run(scenario, repetition):
    return {
        "follower_count": 1,
        "scenario": scenario,
        "run_id": f"run_{repetition:02d}",
        "status": "pass",
        "followers": {"1": {
            "spacing_rmse_m": 0.1,
            "track_fraction": 0.9,
            "collision_samples": 0,
            "control_period_p95_ms": 50.0,
            "inference_latency_p95_ms": 10.0,
        }},
    }


def test_pair_stage_requires_three_runs_per_scenario(tmp_path):
    for scenario in PAIR_SCENARIOS:
        for repetition in range(1, 4):
            run = _passing_run(scenario, repetition)
            path = tmp_path / f"disturbance_1_{scenario}_run_{repetition:02d}_summary.json"
            path.write_text(json.dumps(run), encoding="utf-8")
    assert summarize(tmp_path, "pair")["status"] == "pass"
    assert summarize(tmp_path, "full")["status"] == "fail"
