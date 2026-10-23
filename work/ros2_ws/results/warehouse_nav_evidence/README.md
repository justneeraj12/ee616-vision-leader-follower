# Mapped Warehouse Mission Evidence

This directory is the accepted post-freeze repeatability evidence for the
mapped Nav2 warehouse mission collected on October 23, 2026.

## Protocol

The runner first requires one leader-follower pair to pass. It then runs three
leader-plus-three-follower repetitions. The leader uses a static occupancy map,
AMCL, a 360-degree simulated LiDAR, Nav2 Smac Hybrid-A*, and Regulated Pure
Pursuit. Each follower uses only its forward RGB camera and local wheel
odometry. Gazebo pose truth is consumed only by `ee616_evaluation`.

## Accepted result

- Overall status: pass; one pair run and three full-chain runs.
- Three-run mean transport spacing RMSE: F1 0.1313 m, F2 0.1392 m,
  F3 0.1331 m.
- Worst transport spacing RMSE: F1 0.1526 m, F2 0.1556 m, F3 0.1588 m.
- Minimum TRACK fractions: F1 0.9280, F2 0.9066, F3 0.9026.
- Robot-to-robot collision samples: zero.
- Mapped shelf and wall collision samples: zero.
- Minimum real-time factor: 0.9810.
- Peak container RAM: 3,914 MiB; peak visible GPU memory: 647 MiB.

The numerical source is `summary.json`; per-run CSV and JSON files retain the
raw and derived values. `SHA256SUMS` verifies this directory. The cargo boxes
and load/unload events are scripted visual cues. This experiment does not test
robotic manipulation, measured warehouse throughput, physical robots, or
person safety.
