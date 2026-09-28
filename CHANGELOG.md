# Changelog

This file records reviewable project milestones. Detailed evidence and current limitations remain in [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

## Unreleased

### Added

- VS Code Dev Container configuration for the canonical ROS 2 image
- Integrated build, test, Gazebo GUI, ROS inspection, and stop tasks
- Interactive six-shelf warehouse playground for development
- Developer workflow, project learning maps, and metrics guide
- Canonical Docker environment based on ROS 2 Jazzy and Ubuntu Noble
- ROS 2 workspace with environment and namespace smoke-test nodes
- Minimal headless Gazebo camera world and ROS-Gazebo bridge configuration
- CPU/software-rendering and optional NVIDIA GPU container profiles
- System architecture and reproducible environment documentation

### Verified

- ROS 2 Jazzy workspace builds two packages and passes two package tests
- Isolated `/leader` and `/follower_1` namespace probes pass
- Gazebo Sim 8.15.0 bridges 15 timestamped 640×480 RGB camera samples
- NVIDIA container passthrough exposes the RTX 3050 Ti and 4096 MiB VRAM
- GPU-accelerated Gazebo rendering remains unbenchmarked

### Decisions

- Initial leader uses a deterministic waypoint route and rear visual target
- Leader LiDAR, IMU, odometry, and Nav2 remain a later optional extension
- Followers retain forward RGB camera and local wheel odometry as formation inputs

### Evidence boundary

The environment smoke tests do not constitute camera measurement, follower-control, physical-robot, or safety evidence.

## 0.1.1 2026-09-18

### Added

- Production-style repository README with architecture, verified evidence, quickstart, validation roadmap, and safety boundary
- GitHub Actions testing on Python 3.11 and 3.12
- Contribution guidance and citation metadata

### Changed

- Repository presentation now follows the structure used in Neeraj Kumar Kanchani's recent research and systems repositories
- Reproduction commands consistently use `python3` for the local Ubuntu environment

## 0.1.0 2026-09-18

### Added

- Deterministic single-pair toy simulation with 32 recorded trials
- Multi-follower warehouse maze with one leader and three followers
- Seven automated tests
- Machine-readable summaries, trial metrics, and time series
- Faculty technical explanation, application rationale, figures, and videos
- Project status, decision log, approval log, and standing operating brief
- Private GitHub repository with curated source, evidence, and review deliverables

### Evidence boundary

The 0.1.x results are two-dimensional kinematic evidence. They are not ROS 2, Gazebo, physical-robot, production-readiness, or industrial-safety results.
