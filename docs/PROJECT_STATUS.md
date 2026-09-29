# Project Status

Last updated: September 29, 2026

## Current state

The deterministic Python toy baseline is complete. It includes a single-pair experiment harness and a warehouse-maze demonstration with one leader and three independently controlled followers.

The canonical Docker environment now contains ROS 2 Jazzy, Gazebo Sim 8.15.0, and `ros_gz`. A deterministic fixed-red-target image detector has passed the first static camera range and bearing gate. The GitHub repository is public under AGPL-3.0-only for original project work, with third-party terms preserved separately. No learned-detector, follower-control, physical-robot, or production-safety result has been claimed.

The containerized ROS 2 and Gazebo foundation is complete under `work/ros2_ws/` and `infrastructure/docker/`. The software-rendered and NVIDIA-profile smoke tests passed on the target laptop. The GPU profile verifies container passthrough, but GPU rendering acceleration has not been benchmarked.

The integrated VS Code Dev Container workflow is complete. It adds repeatable build, test, Gazebo GUI, ROS inspection, and shutdown tasks without creating another project workspace.

Five deterministic YAML scenario templates and an optional pinned AWS no-roof warehouse are now available. The templates support controlled Gate 2 experiments. The AWS scene is a visual and resource stress test, not the primary scientific environment.

The camera baseline separates camera geometry from later learned-detection error. The perception node subscribes only to RGB images. A separate evaluation package reads Gazebo poses, moves the target, labels visibility, and records metrics.

The host contains a partial ROS 2 Jazzy installation, but the ROS 2 CLI, Gazebo, and `ros_gz` were not available during inspection. The Docker environment is therefore the canonical implementation environment.

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
- Four ROS 2 packages build with `colcon`, and 19 package tests pass.
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

## Evidence limitations

- Kinematic rather than Gazebo physics
- Idealized follower pose and camera-like measurements
- No learned image detector
- The current detector assumes a fixed-size red target, known target height, static poses, fixed camera calibration, and controlled lighting.
- No ROS 2 control timing, multi-robot load, or full namespace audit beyond the two-node smoke test
- No wheel slip, actuator dynamics, person traffic, or safety-rated obstacle system
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

## Repository state

The project is maintained in the public GitHub repository `justneeraj12/ee616-vision-leader-follower`. Original project software and documentation are licensed under AGPL-3.0-only. The pinned AWS warehouse assets retain their MIT terms, and external reference documents retain their respective terms. The repository includes the governing documentation, source, automated tests, machine-readable evidence, report builders, review deliverables, continuous integration, contribution guidance, and citation metadata. Internal render pages, temporary artifacts, and quality-check screenshots are excluded through `.gitignore`.

## Next proposed approval gate

Implement the approved YOLOv8n measurement evaluation against the same frozen range and bearing matrix after recording the exact dependency, model, dataset, and target-appearance configuration.

## Two gates ahead

1. Integrate one leader and one follower only after the selected learned detector passes the measurement gate.
2. Add followers one at a time and measure spacing-error propagation, corner behavior, minimum separation, and stopping behavior.

## Current blockers

- The fixed-red-target geometry baseline passed, but the proposed YOLOv8n detector, training data, target appearance, and inference timing remain unverified.
- Professor Imtiaz has received the initial report and warehouse video. A follow-up meeting is expected, but technical direction for the next gate has not yet been confirmed.
