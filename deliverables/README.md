# Project Artifacts

This directory contains recorded demonstrations, screenshots, integrity hashes,
and archived outputs from the toy baseline. Numerical claims should be checked
against the machine-readable experiment results rather than inferred from a
video.

## Gazebo demonstrations

| File | Purpose |
|---|---|
| `Neeraj_Kanchani_EE616_Gazebo_Pair_Turn_Demo.mp4` | One leader and one follower during a gradual turn |
| `Neeraj_Kanchani_EE616_Gazebo_Three_Follower_Chain_Demo.mp4` | One leader and three predecessor-following robots |
| `Neeraj_Kanchani_EE616_Gazebo_Recovery_Demo.mp4` | Synthetic RGB blackout, `PREDICT`, `SAFE_STOP`, and reacquisition |
| `Neeraj_Kanchani_EE616_Warehouse_Mission_Demo.mp4` | Sequential loading, convoy transport, gradual turn, and unloading |
| `Neeraj_Kanchani_EE616_Hybrid_AStar_Warehouse_Demo.mp4` | Mapped Nav2 mission through multiple shelf aisles from receiving to dispatch |
| `Neeraj_Kanchani_EE616_Gazebo_Demo_SHA256SUMS.txt` | SHA-256 hashes for the three Gazebo videos |
| `screenshots/` | Full-resolution frames extracted from the Gazebo videos |
| `warehouse_mission_screenshots/` | Full-resolution loading, transport, and drop-off frames |
| `Neeraj_Kanchani_EE616_Warehouse_Mission_SHA256SUMS.txt` | Hashes for the warehouse mission video and frames |
| `warehouse_nav_mission_screenshots/` | Full-resolution receiving, aisle-turn, and dispatch frames |
| `Neeraj_Kanchani_EE616_Hybrid_AStar_Warehouse_SHA256SUMS.txt` | Hashes for the mapped mission video and frames |

## Toy baseline artifacts

| File | Purpose |
|---|---|
| `Neeraj_Kanchani_EE616_Toy_Simulation_2D.mp4` | Single-pair toy-simulator visualization |
| `Neeraj_Kanchani_EE616_Multi_Follower_Warehouse_2D.mp4` | Multi-follower toy warehouse visualization |
| `Neeraj_Kanchani_EE616_Toy_Simulation_Baseline.zip` | Archived single-pair toy baseline |
| `Neeraj_Kanchani_EE616_Multi_Follower_Warehouse_Baseline.zip` | Archived multi-follower toy baseline |

## Evidence rule

The accepted results are indexed in
[`../docs/FINAL_EVIDENCE_INDEX.md`](../docs/FINAL_EVIDENCE_INDEX.md) and stored
under `../work/ros2_ws/results/`. The recorded demonstrations are visual aids;
they do not replace the repeated experiment matrices.

- Pair-turn recording: 0.104 m spacing RMSE, 97.3% `TRACK`, 50 ms
  control-period p95, and zero evaluator collision samples.
- Straight three-follower recording: 0.058, 0.051, and 0.050 m spacing RMSE;
  95%, 99%, and 97% `TRACK`; and zero evaluator collision samples.
- Recovery recording: 1.3 s synthetic blackout, observed `PREDICT` and
  `SAFE_STOP`, zero command during `SAFE_STOP`, 0.40 s reacquisition, and zero
  evaluator collision samples.
- Warehouse mission recording: F1--F3 transport RMSE of 0.075, 0.068, and
  0.050 m; correct load and unload order; 0.972 real-time factor; and zero
  evaluator collision samples.
- Mapped Hybrid-A* recording: F1--F3 transport RMSE of 0.151, 0.122, and
  0.123 m; 92.3%, 93.1%, and 91.3% `TRACK`; all mission checks passed; and
  zero robot or mapped-obstacle collision samples.

The warehouse cargo boxes move through scripted presentation joints. The
mission evaluates convoy transport and stopping order, not grasping or robotic
manipulation.

These are simulation results under the declared evaluator. They do not establish
physical-robot performance, person safety, certification, general string
stability, or production readiness.
