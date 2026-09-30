from ee616_evaluation.pair_gate_evaluator import percentile


def test_percentile_interpolates_and_ignores_nonfinite():
    assert percentile([1.0, 2.0, 3.0, float("nan")], 0.5) == 2.0
    assert percentile([], 0.95) is None
