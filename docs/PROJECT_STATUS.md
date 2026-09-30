# Project Status

Last updated: September 30, 2026

## Current state

The deterministic Python toy baseline is complete. It includes a single-pair experiment harness and a warehouse-maze demonstration with one leader and three independently controlled followers.

The canonical Docker environment now contains ROS 2 Jazzy, Gazebo Sim 8.15.0, and `ros_gz`. A deterministic fixed-red-target image detector passed the first static camera range and bearing gate. The first two YOLOv8n checkpoints failed their independent gates. Diagnosis then found an RGB/BGR runtime mismatch and stale-frame dataset labels. A synchronized v3 dataset and detector corrected those faults and passed a new two-scene sealed measurement gate. The v3 detector then passed the nominal one-pair gate, a staged incremental-chain gate through three followers, a pair-first controlled-disturbance gate, and the target-laptop timing and resource gate. No physical-robot or production-safety result has been claimed.

The containerized ROS 2 and Gazebo foundation is complete under `work/ros2_ws/` and `infrastructure/docker/`. The software-rendered and NVIDIA-profile smoke tests passed on the target laptop. The GPU profile verifies container passthrough, but GPU rendering acceleration has not been benchmarked.

The integrated VS Code Dev Container workflow is complete. It adds repeatable build, test, Gazebo GUI, ROS inspection, and shutdown tasks without creating another project workspace.

Versioned deterministic YAML scenario templates and an optional pinned AWS no-roof warehouse are now available. The templates support controlled Gate 2 experiments. The AWS scene is a visual and resource stress test, not the primary scientific environment.

The camera baseline separates camera geometry from later learned-detection error. The perception node subscribes only to RGB images. A separate evaluation package reads Gazebo poses, moves the target, labels visibility, and records metrics.

The host now runs Ubuntu 26.04.1 LTS and contains a partial ROS 2 Lyrical installation, but the host ROS 2 CLI and Gazebo command were not available during inspection. The project did not migrate to Lyrical and Gazebo Jetty. The versioned Ubuntu Noble container remains the canonical ROS 2 Jazzy and Gazebo Harmonic implementation environment.

The planned seven-gate simulation sequence is complete. Gate 7 freezes the accepted source, protocols, configurations, results, retained detector failures, and evidence boundaries through a machine-verifiable SHA-256 manifest. A separate indexed handbook, walkthrough video, final evidence index, and review archive support operation and faculty review. They do not replace Neeraj's own faculty-facing report.

## Verified evidence

- Seven automated toy-simulation tests pass.
- The multi-follower warehouse run is deterministic for its recorded seed.
- The nominal 86-second run completed seven path segments.
- The run recorded zero collision samples in the toy collision model.
- Spacing RMSE was 0.140 m, 0.164 m, and 0.200 m from Follower 1 through Follower 3.
- Faculty-facing DOCX and PDF reports have been rendered and visually checked.
- The eight-page initial technical explanation contains four traceable figures and has been rendered and visually checked page by page.
- A two-dimensional warehouse demonstration video is available in `deliverables/`.
- The GitHub repository is public at `https://github.com/justneeraj12/ee616-vision-leader-follower` under AGPL-3.0-only for original project work.
- The repository includes a production-style README, reproducible quickstart, contribution guidance, citation metadata, and GitHub Actions testing for Python 3.11 and 3.12.
- A separate five-page, single-column IEEEtran technical report has been compiled from LaTeX and visually checked page by page. It uses simple formal English and preserves the existing evidence boundaries.
- Five ROS 2 packages build with `colcon`, and 54 package tests pass.
- The `/leader` and `/follower_1` namespace probes each received five local heartbeat samples.
- Gazebo produced 15 timestamped 640×480 RGB images through the ROS bridge.
- The NVIDIA container profile sees the RTX 3050 Ti, driver 595.91.07, and 4096 MiB VRAM.
- The Dev Container starts as the non-root `ubuntu` user with `/home/ubuntu` as its home directory.
- The warehouse playground opens in the Gazebo GUI and its bridged camera produced 15 timestamped 640×480 RGB samples in the persistent Dev Container.
- The integrated stop task removed the Gazebo and bridge processes cleanly.
- All five deterministic scenarios generated valid SDF and delivered 30 timestamped 640×480 RGB frames through the ROS bridge.
- The AWS no-roof warehouse delivered 150 of 150 camera frames at 15.19 Hz with a median real-time factor of 0.9999 and no fatal asset or plugin errors.
- During the 20-second AWS measurement window, peak container memory was 364.7 MiB, CPU use was 47.9% of one core equivalent, visible NVIDIA memory was 253 MiB, and peak reported GPU utilization was 19%.
- The fixed-target camera experiment retained 2,520 samples across an open calibration scene and a structured aisle.
- Across 1,620 full-visible samples, the valid measurement rate was 100%.
- Combined range RMSE was 0.0355 m, and combined bearing MAE was 0.120 degrees.
- Gazebo ground truth was read only by `ee616_evaluation`; it was not published to the perception node.
- After the Ubuntu 26.04.1 host upgrade, the full environment gate passed again: four ROS packages built, 19 ROS tests passed, both namespace probes passed, and Gazebo delivered 15 timestamped 640×480 RGB frames.
- PyTorch 2.9.1 performed a CUDA tensor operation inside the GPU profile on the RTX 3050 Ti; seven toy-simulation tests also passed.
- The YOLOv8n starting checkpoint is 6,549,796 bytes with SHA-256 `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36`.
- The dataset recorder retained 648 labeled Gazebo images: 324 training, 162 validation, and 162 held-out dataset-test images. Scenario-level separation prevents a scene from appearing in more than one split.
- The dataset has 264 positive and 60 negative training labels, 132 positive and 30 negative validation labels, and 132 positive and 30 negative test labels. Its aggregate SHA-256 is `1049c1491947995b3439d482c6f2bcc86425d52d31d05cc9b43ba92be9e6579a`.
- The isolated YOLO perception backend subscribes only to RGB images and publishes range, bearing, validity, and inference latency. Ground-truth dependency tests cover every perception module.
- The trained YOLOv8n checkpoint has SHA-256 `5bc35221ce82e95b843196551d4a4ee2d2074dce98e42685df3fbef9bb1f541a`. On the held-out dataset test, it recorded 123 true positives, 28 true negatives, nine false negatives, and two false positives.
- The frozen measurement gate retained 2,520 YOLO samples. Of 1,620 full-visible samples, 1,290 were valid, for a 79.6% valid rate. Range RMSE was 0.505 m, bearing MAE was 0.153 degrees, and p95 inference latency was 9.13 ms. The overall gate failed.
- During the measurement gate, peak container memory was 1,474.1 MiB, peak visible GPU memory was 2,241 MiB, peak GPU utilization was 41%, and CPU use was 60.5% of one core equivalent.
- The corrective detector dataset contains 1,125 images: 675 training, 225 validation, and 225 held-out test images. No identical image crosses a split. Its aggregate SHA-256 is `e42368ae861b468206a9f7bec435508a214bc46e333f8c891b87f2cd50a00e15`.
- Corrective YOLOv8n training stopped at epoch 40 and retained best epoch 28. The checkpoint SHA-256 is `cd949c617eaff472417425db025b03fc5b6c9b7698d884cdc7c8562ee930bf62`.
- The corrective held-out dataset test recorded 166 true positives, 23 true negatives, 25 false negatives, and 11 false positives. Validation-only calibration reduced validation range RMSE from 0.083 m to 0.051 m on 97 detected full-visible samples.
- The unchanged final gate retained 2,520 samples and 1,620 full-visible samples but produced zero valid corrective-detector measurements. Inference latency passed at 7.35 ms p95. Range and bearing errors were undefined, so the overall gate failed.
- During corrective training, peak container memory was 3,035.3 MiB and peak visible GPU memory was 3,366 MiB. During the final gate, the corresponding peaks were 1,182.6 MiB and 2,027 MiB.
- The synchronized v3 dataset contains 1,001 images: 715 training, 143 validation, and 143 held-out test images. No identical image crosses a split. Its aggregate SHA-256 is `574c362dd6877cfc63079b959029ae4e2e0c184b294154f759b498a7fb158a33`.
- An offline visibility audit removed 39 fully occluded or unrendered projected labels. All 1,001 final image-label pairs passed the alignment audit.
- Synchronized YOLOv8n v3 completed 50 epochs and retained best epoch 49. The checkpoint SHA-256 is `3ceabbabd0bccf721fcd9954b4eaffebef7b05f2572e43393a1df7568707391a`.
- Validation-only selection chose confidence 0.40. Calibration used 58 correctly localized full-visible validation samples and reduced range RMSE from 0.0783 m to 0.0251 m.
- The v3 held-out dataset test recorded 104 correctly localized positives, 31 true negatives, two missed positives, six mislocalized positives, and zero false positives. Localization-aware recall was 92.9%.
- The v3 sealed measurement gate retained 2,520 samples and all 1,620 full-visible samples were valid. Range RMSE was 0.0323 m, bearing MAE was 0.1569 degrees, and p95 inference latency was 9.02 ms. All approved limits passed.
- During v3 training, peak container memory was 3,085.7 MiB and peak visible GPU memory was 3,623 MiB. During its sealed gate, the corresponding peaks were 1,577.7 MiB and 2,320 MiB.
- The nominal one-pair gate completed three straight and three gradual-turn runs with isolated `/leader` and `/follower_1` namespaces.
- Worst spacing RMSE was 0.0558 m for straight motion and 0.1005 m for gradual turns. The minimum TRACK fraction was 99.1%, and zero collision samples were recorded under the defined evaluator.
- The worst p95 control period was 50.0 ms. The six-run resource window used 1,330.8 MiB peak container memory, 383 MiB peak visible GPU memory, 27% peak GPU utilization, and 152.1% of one CPU-core equivalent.
- Pair-gate ground truth was read only by `ee616_evaluation`; the controller subscribed only to the learned relative measurement and local wheel odometry.
- The incremental-chain gate completed six two-follower runs before permitting six three-follower runs. All 12 nominal straight and gradual-turn runs passed.
- In the three-follower matrix, worst spacing RMSE was 0.1004 m, 0.0739 m, and 0.0523 m from Follower 1 through Follower 3. Minimum TRACK fraction was 95.0%, worst p95 control period was 50.0 ms, and the evaluator recorded zero collision samples.
- Mean spacing RMSE decreased toward the rear in the nominal Gazebo matrix. Rearward error amplification was not observed, so the earlier toy-model trend is not claimed for this gate.
- The 335.4-second chain resource window used 3,376.6 MiB peak container memory, 736 MiB peak visible GPU memory, 60% peak GPU utilization, and 264.3% of one CPU-core equivalent.
- Chain-gate Gazebo truth was consumed only by `ee616_evaluation`; each follower controller used its own RGB measurement and local wheel odometry under an isolated namespace.
- The controlled-disturbance gate completed 15 pair runs before permitting three combined three-follower runs. All 18 runs passed the frozen checks.
- Pair worst spacing RMSE was 0.1247 m for the sharp turn, 0.0579 m for short occlusion, 0.0906 m for long occlusion, 0.0882 m for a stopped leader, and 0.0536 m for actuator bias.
- In the combined three-follower runs, worst spacing RMSE was 0.1007 m, 0.1242 m, and 0.1403 m from Follower 1 through Follower 3. This matrix showed rearward error growth.
- All disturbance runs recorded zero evaluator collision samples. Worst p95 control period was 50.0 ms, and combined-run p95 detector latency was at most 17.1 ms.
- Long visual loss produced `PREDICT`, `SAFE STOP`, zero command during `SAFE STOP`, and later `TRACK` reacquisition in every repeated pair and combined run.
- The 620.0-second disturbance resource window used 3,511.9 MiB peak container memory, 642 MiB peak visible GPU memory, 51% peak GPU utilization, and 217.1% of one CPU-core equivalent.
- Disturbance-gate Gazebo truth remained inside `ee616_evaluation`; full-frame RGB blackouts and the post-controller yaw-command bias did not consume truth.
- The target-laptop timing gate completed three accepted combined three-follower runs. All three timing summaries and all three behavior summaries passed the frozen checks.
- Across the timing matrix, worst p95 camera-to-measurement latency was 23.09 ms, valid-measurement-to-controller latency was 48.35 ms, controller-to-post-proxy command latency was 2.89 ms, detector inference time was 20.34 ms, and control period was 50.0 ms.
- Minimum measurement delivery ratio was 95.4%, and minimum simulation real-time factor was 0.9996.
- The 158.9-second timing resource window used 3,584.0 MiB peak container memory, 642 MiB peak visible GPU memory, 60% peak GPU utilization, and 443.1% of one CPU-core equivalent across 12 logical CPUs.
- The timing observer used ROS topics only. Gazebo pose truth remained confined to the separate behavior evaluator. These are one-laptop simulation measurements, not network or physical-actuator timing.
- Five ROS 2 packages build and 59 package tests pass after the Gate 6 evaluator-lifecycle repair.
- The final verification rerun built all five ROS packages and passed 59 package tests with zero failures; all seven toy tests also passed.
- The Gate 7 technical handbook compiled to 68 pages with a generated index and passed full-page visual inspection.
- The Gate 7 evidence walkthrough is a verified 1920×1080, 30 fps, 40-second MP4.
- The Gate 7 manifest verifies expected pass/fail evidence states and SHA-256 checksums for the frozen file set.

## Evidence limitations

- The toy baseline is kinematic and uses idealized camera-like measurements; the new pair gate is separate Gazebo-physics evidence.
- The first two learned-detector attempts remain failed evidence; v3 passed the defined static, nominal moving, and controlled-disturbance simulation gates.
- The current detector still assumes a fixed-size red target, known target height, fixed camera calibration, and controlled lighting.
- Chain evidence is limited to at most three followers and the frozen nominal and combined disturbance routes.
- The nominal chain showed decreasing mean RMSE toward the rear, while the combined disturbance matrix showed increasing mean RMSE. Neither result establishes general string stability.
- Visual occlusion was a synthetic full-frame RGB blackout, not a physical occluding object. The actuator disturbance was a bounded yaw-command bias, not wheel slip or a motor fault.
- During stopped-leader runs, final commands settled near zero but the pair retained about 0.12 m of short-gap undershoot because the controller does not reverse.
- No wheel slip, detailed actuator dynamics, person traffic, or safety-rated obstacle system
- No physical robot validation or certification claim
- The Gazebo GUI used Mesa/GLX/EGL fallback paths during verification; GPU-accelerated rendering performance remains unverified.
- The AWS benchmark does not run a detector, range or bearing estimator, follower controller, collision experiment, or safety test.

## Current deliverables

- Initial technical explanation and preliminary figures in DOCX and PDF
- Single-column IEEE LaTeX technical report in PDF, with editable source under `work/ieee_simple_report/`
- Industry application and system rationale in DOCX and PDF
- Initial toy simulation results in DOCX and PDF
- Multi-follower warehouse demonstration video
- Single-follower toy demonstration video
- Reproducible baseline ZIP packages
- Verified container and ROS 2 workspace foundation with machine-readable environment evidence
- VS Code Dev Container workflow, six-shelf Gazebo learning playground, architecture maps, and metric study guide
- Deterministic scenario matrix, repeatable five-scenario transport validator, and optional AWS warehouse resource benchmark
- Camera-only red-target perception package, isolated evaluation package, raw CSV evidence, JSON summaries, and error figure
- Three versioned YOLOv8n experiment designs, local separated datasets and manifests, starting-model checksum, and isolated perception backend
- Three trained YOLOv8n checkpoints, held-out dataset tests, sealed measurement rows, failure and pass summaries, timing data, resource logs, and corrective diagnostics
- Nominal one-pair ROS control package, dynamic Gazebo models, six-run raw logs and summaries, resource evidence, and a traceable result figure
- Nominal incremental-chain worlds, isolated follower instances, 12-run raw logs and summaries, resource evidence, and a traceable result figure
- Controlled-disturbance proxy, pair-first 18-run matrix, raw logs, summaries, resource evidence, checksums, and a traceable result figure
- Target-laptop timing observer, three-run raw timing logs, behavior summaries, resource time series, aggregate summary, checksums, and traceable figure
- Final evidence index and machine-verifiable Gate 7 freeze manifest
- 68-page indexed LaTeX project handbook and simulation user guide
- Gate 7 evidence walkthrough video and frozen repository review ZIP

## Repository state

The project is maintained in the public GitHub repository `justneeraj12/ee616-vision-leader-follower`. Original project software and documentation are licensed under AGPL-3.0-only. The pinned AWS warehouse assets retain their MIT terms, and external reference documents retain their respective terms. The repository includes the governing documentation, source, automated tests, machine-readable evidence, report builders, review deliverables, continuous integration, contribution guidance, and citation metadata. Internal render pages, temporary artifacts, and quality-check screenshots are excluded through `.gitignore`.

## Gate sequence status

All seven planned simulation gates are complete. Faculty-facing report prose remains Neeraj's writing unless he explicitly approves a defined drafting task. Any new technical direction begins as a separately approved change rather than altering the frozen results.

## Current blockers

- No blocker remains inside the approved seven-gate simulation scope.
- Physical-robot validation is unverified and was not part of these gates.
- Professor Imtiaz may request a changed scope after review; no such change is assumed in the frozen package.
