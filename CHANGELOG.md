# Changelog

This file records reviewable project milestones. Detailed evidence and current limitations remain in [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

## Unreleased

### Changed

- Repository navigation now presents the implementation, tests, evidence, and
  demonstrations without a separate review package
- Live demonstration commands use neutral `gazebo-demo` names

### Removed

- Generated report, handbook, review-packet, and report-builder artifacts

### Added

- Mapped three-row warehouse with separate receiving and dispatch docks
- Leader-only Nav2 AMCL, LiDAR, Smac Hybrid-A*, and Regulated Pure Pursuit
- Pair-first mapped-mission repeatability runner, result plot, checksums, and
  retained failed target-association development evidence
- One-command mapped warehouse GUI and recording mode
- VS Code Dev Container configuration for the canonical ROS 2 image
- Integrated build, test, Gazebo GUI, ROS inspection, and stop tasks
- Interactive six-shelf warehouse playground for development
- Developer workflow, project learning maps, and metrics guide
- Canonical Docker environment based on ROS 2 Jazzy and Ubuntu Noble
- ROS 2 workspace with environment and namespace smoke-test nodes
- Minimal headless Gazebo camera world and ROS-Gazebo bridge configuration
- CPU/software-rendering and optional NVIDIA GPU container profiles
- System architecture and reproducible environment documentation
- Deterministic YAML scenario generator and five controlled warehouse conditions
- Pinned AWS no-roof warehouse subset with source provenance and license
- Repeatable scenario transport and AWS laptop-resource benchmarks

### Verified

- One mapped pair run and three full mapped warehouse runs passed with zero
  robot or mapped-obstacle collision samples
- Mapped full-chain mean spacing RMSE was 0.1313 m, 0.1392 m, and 0.1331 m;
  minimum real-time factor was 0.9810
- ROS 2 Jazzy workspace builds two packages and passes six package tests
- Isolated `/leader` and `/follower_1` namespace probes pass
- Gazebo Sim 8.15.0 bridges 15 timestamped 640×480 RGB camera samples
- NVIDIA container passthrough exposes the RTX 3050 Ti and 4096 MiB VRAM
- GPU-accelerated Gazebo rendering remains unbenchmarked
- All five controlled scenarios deliver timestamped 640×480 RGB frames
- AWS no-roof benchmark passes at 0.9999 median real-time factor with 364.7 MiB peak container memory

### Decisions

- Use Hybrid-A* rather than RRT-Connect for the known 2-D warehouse map and
  differential-drive leader; keep all route planning off the followers
- The frozen baseline leader retains its deterministic waypoint route; the
  post-freeze mapped mission adds leader-only Nav2, LiDAR, and odometry
- Followers retain forward RGB camera and local wheel odometry as formation inputs
- Controlled scenarios are primary Gate 2 environments; the AWS world is an optional visual and resource stress test

### Evidence boundary

The environment and scenario smoke tests do not constitute camera-accuracy, detector, follower-control, physical-robot, or safety evidence.

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
- Technical explanation, application rationale, figures, and videos
- Project status, decision log, approval log, and standing operating brief
- Private GitHub repository with curated source, evidence, and review deliverables

### Evidence boundary

The 0.1.x results are two-dimensional kinematic evidence. They are not ROS 2, Gazebo, physical-robot, production-readiness, or industrial-safety results.
