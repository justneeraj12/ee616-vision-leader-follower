from math import radians

from ee616_evaluation.dataset_labels import project_target_box
from ee616_evaluation.pose_text import EntityPose


def test_projects_centered_target_to_valid_yolo_box():
    box = project_target_box(
        EntityPose(0.0, 0.0, 0.65, 0.0),
        EntityPose(3.0, 0.0, 0.6, 0.0),
        (0.08, 0.70, 0.90),
        image_width=640,
        image_height=480,
        horizontal_fov_rad=radians(70.0),
    )
    assert box is not None
    assert 0.49 < box.center_x < 0.51
    assert 0.0 < box.width < 1.0
    assert 0.0 < box.height < 1.0


def test_target_fully_outside_horizontal_field_has_no_box():
    box = project_target_box(
        EntityPose(0.0, 0.0, 0.65, 0.0),
        EntityPose(3.0, 6.0, 0.6, 0.0),
        (0.08, 0.70, 0.90),
        image_width=640,
        image_height=480,
        horizontal_fov_rad=radians(70.0),
    )
    assert box is None


def test_yolo_line_has_class_and_normalized_fields():
    box = project_target_box(
        EntityPose(0.0, 0.0, 0.65, 0.0),
        EntityPose(2.0, -0.5, 0.6, 0.0),
        (0.08, 0.70, 0.90),
        image_width=640,
        image_height=480,
        horizontal_fov_rad=radians(70.0),
    )
    assert box is not None
    fields = box.label_line(0).split()
    assert fields[0] == "0"
    assert len(fields) == 5
    assert all(0.0 <= float(value) <= 1.0 for value in fields[1:])
