# Project Status

Last updated: September 28, 2026

## Current state

The deterministic Python toy baseline is complete. It includes a single-pair experiment harness and a warehouse-maze demonstration with one leader and three independently controlled followers.

The canonical Docker environment now contains ROS 2 Jazzy, Gazebo Sim 8.15.0, and `ros_gz`. No detector, inference, camera-accuracy, or follower-control result has been claimed.

The containerized ROS 2 and Gazebo foundation is complete under `work/ros2_ws/` and `infrastructure/docker/`. The software-rendered and NVIDIA-profile smoke tests passed on the target laptop. The GPU profile verifies container passthrough, but GPU rendering acceleration has not been benchmarked.

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
- A private GitHub repository has been created at `https://github.com/justneeraj12/ee616-vision-leader-follower`.
- The repository includes a production-style README, reproducible quickstart, contribution guidance, citation metadata, and GitHub Actions testing for Python 3.11 and 3.12.
- A separate five-page, single-column IEEEtran technical report has been compiled from LaTeX and visually checked page by page. It uses simple formal English and preserves the existing evidence boundaries.
- Two ROS 2 packages build with `colcon`, and two package tests pass.
- The `/leader` and `/follower_1` namespace probes each received five local heartbeat samples.
- Gazebo produced 15 timestamped 640×480 RGB images through the ROS bridge.
- The NVIDIA container profile sees the RTX 3050 Ti, driver 595.91.07, and 4096 MiB VRAM.

## Evidence limitations

- Kinematic rather than Gazebo physics
- Idealized follower pose and camera-like measurements
- No learned image detector
- No ROS 2 control timing, multi-robot load, or full namespace audit beyond the two-node smoke test
- No wheel slip, actuator dynamics, person traffic, or safety-rated obstacle system
- No physical robot validation or certification claim

## Current deliverables

- Initial technical explanation and preliminary figures in DOCX and PDF
- Single-column IEEE LaTeX technical report in PDF, with editable source under `work/ieee_simple_report/`
- Industry application and system rationale in DOCX and PDF
- Initial toy simulation results in DOCX and PDF
- Multi-follower warehouse demonstration video
- Single-follower toy demonstration video
- Reproducible baseline ZIP packages
- Verified container and ROS 2 workspace foundation with machine-readable environment evidence

## Repository state

The project is maintained in the private GitHub repository `justneeraj12/ee616-vision-leader-follower`. The repository includes the governing documentation, source, automated tests, machine-readable evidence, report builders, review deliverables, continuous integration, contribution guidance, and citation metadata. Internal render pages, temporary artifacts, and quality-check screenshots are excluded through `.gitignore`.

## Next proposed approval gate

Request approval for the measurement-only camera experiment that compares estimated range and bearing with evaluation-only Gazebo ground truth.

## Two gates ahead

1. Integrate one leader and one follower with estimator, bounded controller, and TRACK, PREDICT, and SAFE STOP states.
2. Add followers one at a time and measure spacing-error propagation, corner behavior, minimum separation, and stopping behavior.

## Current blockers

- The final leader visual target and camera measurement model have not been selected through Gazebo evidence.
- Professor Imtiaz has received the initial report and warehouse video. A follow-up meeting is expected, but technical direction for the next gate has not yet been confirmed.
- The GitHub repository is private and has not been presented as a public release.
