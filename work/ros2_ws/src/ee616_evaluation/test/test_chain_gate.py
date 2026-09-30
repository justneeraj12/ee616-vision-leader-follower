import json

from ee616_evaluation.summarize_chain_gate import summarize


def _run(count, profile, repetition):
    return {
        "follower_count": count,
        "profile": profile,
        "run_id": f"run_{repetition:02d}",
        "status": "pass",
        "followers": {
            str(index): {
                "spacing_rmse_m": 0.05 + index * 0.01,
                "track_fraction": 1.0,
                "collision_samples": 0,
                "control_period_p95_ms": 50.0,
                "inference_latency_p95_ms": 8.0,
            }
            for index in range(1, count + 1)
        },
    }


def test_stage_two_requires_six_passing_runs(tmp_path):
    for profile in ("straight", "turn"):
        for repetition in range(1, 4):
            run = _run(2, profile, repetition)
            path = tmp_path / f"chain_2_{profile}_run_{repetition:02d}_summary.json"
            path.write_text(json.dumps(run), encoding="utf-8")
    summary = summarize(tmp_path, max_followers=2)
    assert summary["status"] == "pass"
    assert summary["chains"]["2"]["mean_rearward_rmse_delta_m"]["follower_1_to_2"] > 0.0


def test_full_gate_rejects_missing_three_follower_stage(tmp_path):
    assert summarize(tmp_path, max_followers=3)["status"] == "fail"
