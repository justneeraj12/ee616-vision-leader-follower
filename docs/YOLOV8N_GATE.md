# YOLOv8n Measurement Gate

## Purpose

This gate tests whether a small learned detector can find the predecessor's rear target from a forward RGB image. It does not test follower control. The detector output is a bounding box. Known target height and camera calibration convert that box into range and bearing.

## Frozen target

The class name is `predecessor_target`. The target is the same solid red plate used by the A012 geometry baseline. It is 0.70 m wide and 0.90 m high. Its thickness is 0.08 m. Keeping the geometry unchanged allows a direct comparison between pixel segmentation and YOLO detection.

## Dataset separation

The dataset uses scenario-level separation:

- Training: `yolo_train_open` and `yolo_train_aisle`
- Validation: `yolo_val_mixed`
- Dataset test: `yolo_test_occlusion`
- Final measurement gate: `camera_calibration` and `straight_aisle`

The final A012 scenes are not used for training, validation, or dataset testing. The recorder belongs to `ee616_evaluation`. It may use Gazebo poses to generate offline labels. `ee616_perception` has no Gazebo pose dependency.

Each label covers the projected full target extent and is clipped at the image boundary. A fully out-of-frame target receives an empty label. The held-out occlusion scene keeps the full target box even where the foreground object hides part of the plate.

## Reproducible commands

Acquire and fingerprint the named starting checkpoint:

```bash
make yolo-model-acquire
```

Generate and validate the 648-image dataset:

```bash
make yolo-dataset-capture
```

Train with the recorded 4 GB-VRAM configuration and run the frozen gate:

```bash
make yolo-train
make yolo-gate
```

The images and labels remain local under `work/ros2_ws/datasets/`. The aggregate dataset manifest is retained under `work/ros2_ws/results/yolo_dataset/`. The complete frozen design is in `work/ros2_ws/experiments/yolov8n_gate/experiment.yaml`.

## Evidence boundary

Dataset generation and backend implementation are not accuracy results. The required limits are at least 95% valid full-visible measurements, range RMSE no more than 0.15 m, bearing MAE no more than 1.5 degrees, and p95 detector latency no more than 66.7 ms.

## Recorded result

Training attempt 1 reached epoch 26 and stopped with a CUDA out-of-memory error. Its logs and checkpoints were preserved. Attempt 2 used batch 4 and one worker. Early stopping selected epoch 29. The retained checkpoint SHA-256 is `5bc35221ce82e95b843196551d4a4ee2d2074dce98e42685df3fbef9bb1f541a`.

The final matrix recorded 2,520 samples, including 1,620 full-visible samples. The valid full-visible rate was 79.6%, range RMSE was 0.505 m, bearing MAE was 0.153 degrees, and p95 inference latency was 9.13 ms. Bearing and latency passed. Valid rate and range failed. The overall result is a failed gate, and this checkpoint must not enter follower control.

The held-out dataset test recorded 123 true positives, 28 true negatives, nine false negatives, and two false positives. The final measurement gate recorded 330 invalid full-visible samples. Non-full-visible samples are not labeled as false positives because that group mixes cropped, partial, occluded, and out-of-frame targets.

## Corrective v2 result

The approved corrective stage added confidence and box diagnostics, explicit 1.0 m coverage, a low-light training scene, and wider range and bearing variation. Its separate dataset contains 1,125 images: 675 training, 225 validation, and 225 held-out test images. The manifest reports zero identical images across dataset splits and aggregate SHA-256 `e42368ae861b468206a9f7bec435508a214bc46e333f8c891b87f2cd50a00e15`.

Corrective training stopped at epoch 40 and retained best epoch 28. The checkpoint SHA-256 is `cd949c617eaff472417425db025b03fc5b6c9b7698d884cdc7c8562ee930bf62`. Its held-out dataset test recorded 166 true positives, 23 true negatives, 25 false negatives, and 11 false positives. A linear range correction fitted on 97 validation detections reduced validation range RMSE from 0.083 m to 0.051 m. No final-gate image contributed to training or calibration.

The unchanged final matrix retained 2,520 samples and 1,620 full-visible samples. It produced zero valid measurements. Inference latency passed at 7.35 ms p95, but range and bearing errors were undefined. Therefore, the corrective checkpoint also fails and must not enter follower control. The separated dataset result did not generalize to the independent final scenes.

Reproduce the corrective artifacts with:

```bash
make yolo-dataset-v2
make yolo-train-v2
make yolo-gate-v2
```

## Synchronized v3 result

Post-gate diagnosis found two implementation faults. The ROS node converted camera messages to RGB but passed the array to an inference interface that expects BGR. The v2 recorder also waited only two camera frames after moving the target, so some images and projected labels described different poses. The failed v1 and v2 evidence is preserved; neither checkpoint is reused.

The v3 recorder waits eight frames per pose. Its separated dataset contains 1,001 images: 715 training, 143 validation, and 143 held-out test images. An offline rendered-target visibility check removed 39 fully occluded or unrendered pose projections. The final alignment audit checked all 1,001 image-label pairs and passed. No identical image crosses a split. The aggregate dataset SHA-256 is `574c362dd6877cfc63079b959029ae4e2e0c184b294154f759b498a7fb158a33`.

Training completed 50 epochs and selected epoch 49. The checkpoint SHA-256 is `3ceabbabd0bccf721fcd9954b4eaffebef7b05f2572e43393a1df7568707391a`. Validation-only selection chose confidence 0.40. A linear range calibration fitted on 58 correctly localized full-visible validation samples reduced validation range RMSE from 0.0783 m to 0.0251 m. The held-out dataset test recorded 104 correctly localized positives, 31 true negatives, two misses, six mislocalized positives, and zero false positives.

Two new final scenes were hashed and sealed before training. They contributed no image to training, validation, threshold selection, or calibration. The sealed matrix retained 2,520 samples and 1,620 full-visible samples. All full-visible samples were valid. Range RMSE was 0.0323 m, bearing MAE was 0.1569 degrees, and p95 inference latency was 9.02 ms. All four approved limits passed.

This result validates static RGB target detection and relative measurement in the two sealed Gazebo scenes. It does not validate estimation, closed-loop following, multi-robot behavior, physical robots, or safety.

Reproduce the v3 artifacts with:

```bash
make yolo-dataset-v3
make yolo-train-v3
make yolo-gate-v3
```
