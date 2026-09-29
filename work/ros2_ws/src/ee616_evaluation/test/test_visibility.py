from ee616_evaluation.visibility import line_blocked, segment_intersects_box


BOX = (4.0, 2.5, 0.0, 3.0, 1.0)


def test_segment_entering_shelf_is_blocked():
    assert segment_intersects_box(0.0, 0.0, 5.0, 2.5, BOX)


def test_clear_aisle_segment_is_not_blocked():
    assert not segment_intersects_box(0.0, 0.0, 5.0, 0.0, BOX)


def test_any_obstacle_can_block_line_of_sight():
    assert line_blocked(0.0, 0.0, 5.0, 2.5, [BOX])
    assert not line_blocked(0.0, 0.0, 3.0, 0.0, [BOX])
