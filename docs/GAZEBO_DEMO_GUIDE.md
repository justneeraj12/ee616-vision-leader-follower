# Gazebo Demonstration Guide

This guide runs the live presentation views added after the Gate 7 evidence
freeze. They reuse the accepted ROS 2 packages, YOLOv8n v3 detector, estimator,
controller, and evaluator. They do not modify or replace the frozen Gate 1--7
results.

## What to show

| Mode | Purpose | Recorded result |
|---|---|---|
| `pair_turn` | One leader and one follower during a gradual turn | Passed: 0.104 m spacing RMSE, 97.3% `TRACK`, 50 ms control-period p95, zero collision samples |
| `chain_straight` | One leader and three independently driven followers in predecessor-following order | Passed: 0.058, 0.051, and 0.050 m spacing RMSE; 95%, 99%, and 97% `TRACK`; zero collision samples |
| `recovery` | One validated pair during a 1.3-second synthetic RGB blackout | Passed: `PREDICT` and `SAFE STOP` observed; zero command in `SAFE STOP`; 0.40 s reacquisition; zero collision samples |
| `warehouse_mission` | Sequential loading, gradual-turn convoy transport, and sequential unloading | Passed: F1--F3 transport RMSE 0.075, 0.068, and 0.050 m; correct load/unload order; zero collision samples |
| `warehouse_nav_mission` | Mapped receiving-to-dispatch mission through multiple aisles and turns | Pair-first repeatability gate passed; three-run mean RMSE was 0.131, 0.139, and 0.133 m; zero robot or mapped-obstacle collision samples |

The chain view shows Follower 1's RGB image and the supervisor state of all
three followers. This reduces presentation-only observer load. Each follower's
normal detector still receives its own camera stream.

## Start a live demonstration

Run these commands from the project root on the logged-in Hyprland desktop:

```bash
./launchers/pair_turn.sh
./launchers/chain_straight.sh
./launchers/chain_turn.sh
./launchers/recovery.sh
./launchers/warehouse_mission.sh
./launchers/warehouse_nav_mission.sh
```

The executable wrappers resolve the project root automatically, so they also
work when called by absolute path from another directory. The equivalent manual
commands are:

```bash
make gazebo-demo DEMO_MODE=pair_turn
make gazebo-demo DEMO_MODE=chain_straight
make gazebo-demo DEMO_MODE=chain_turn
make gazebo-demo DEMO_MODE=recovery
make gazebo-demo DEMO_MODE=warehouse_mission
make gazebo-demo DEMO_MODE=warehouse_nav_mission
```

Each command builds the four required ROS packages, opens Gazebo Sim and the
read-only dashboard, runs one bounded experiment, writes a timestamped result
below `work/ros2_ws/results/demo_runs/`, and closes the windows when the
evaluator completes.

The equivalent VS Code task is **EE616: Launch Gazebo demonstration**. It
prompts for the mode. Use **EE616: Open demo inspection shell** to
inspect ROS topics during a separate live run.

## Record a video

```bash
make gazebo-demo-record DEMO_MODE=pair_turn
make gazebo-demo-record DEMO_MODE=chain_straight
make gazebo-demo-record DEMO_MODE=recovery
make gazebo-demo-record DEMO_MODE=warehouse_mission
make gazebo-demo-record DEMO_MODE=warehouse_nav_mission
```

The recorder moves the Gazebo and dashboard windows to Hyprland workspace 9,
records the focused monitor at 1920 by 1080 and 30 frames per second, then
returns to the previous workspace. It uses VA-API hardware encoding on
`/dev/dri/renderD128` when available and falls back to CPU encoding otherwise.
Set `EE616_RECORD_MONITOR` to a Hyprland monitor name if the automatic focused
monitor is not the desired one.

The output files include:

- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Pair_Turn_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Three_Follower_Chain_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Gazebo_Recovery_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Warehouse_Mission_Demo.mp4`
- `deliverables/Neeraj_Kanchani_EE616_Hybrid_AStar_Warehouse_Demo.mp4`

Verify the final files from `deliverables/` with:

```bash
sha256sum -c Neeraj_Kanchani_EE616_Gazebo_Demo_SHA256SUMS.txt
sha256sum -c Neeraj_Kanchani_EE616_Hybrid_AStar_Warehouse_SHA256SUMS.txt
```

## What the windows mean

Gazebo shows the simulated world, leader, followers, and their physical motion.
The dashboard subscribes to existing ROS topics and publishes nothing into the
robot stack. Its header shows the current supervisor state and experiment event.

- `TRACK`: a recent valid camera measurement updates the estimate.
- `PREDICT`: the measurement is temporarily missing, so the estimator predicts
  for a bounded interval.
- `SAFE_STOP`: the estimate is stale, so the follower commands zero linear and
  angular velocity.
- A black dashboard image during `LONG_OCCLUSION` is an intentional synthetic
  full-frame blackout, not a rendering failure.

Gazebo pose truth is read only by `ee616_evaluation` to calculate metrics. It is
not published to detection, estimation, supervision, control, or the disturbance
proxy.

## Interpretation

For the pair video: "This is the minimum scientific unit. The leader owns the
route. The follower uses its forward RGB camera and local odometry. Gazebo pose
data is used only by the evaluator."

For the chain video: "Each follower runs the same isolated pipeline and tracks
only its immediate predecessor. This video demonstrates the three-follower
topology in a straight aisle. The frozen experiment matrix contains repeated
straight and turn trials."

For the recovery video: "I intentionally remove the RGB image for 1.3 seconds.
The controller first predicts for a bounded time, then commands a safe stop when
the estimate becomes stale, and returns to tracking after the target reappears."

For the warehouse mission: "The robots enter the loading point in order, carry
visible scripted cargo through a gradual aisle transition, and stop at the
drop-off point. The leader owns the route. Every follower still uses only its
own forward RGB camera and wheel odometry for control. The cargo lift is a
visual mission cue; this project does not claim autonomous manipulation."

For the mapped mission: "The leader localizes on a warehouse map with AMCL,
uses LiDAR for navigation obstacles, plans a kinematically feasible route with
Nav2 Smac Hybrid-A*, and executes it with Regulated Pure Pursuit. Each follower
still tracks only its immediate predecessor using its RGB camera and local
odometry. Loading and unloading are scripted visual events, not grasping."

Use the words "simulated," "recorded," and "under this defined evaluator."
Do not say that these videos prove physical-robot performance, person safety,
certification, general string stability, or production readiness.

## Gazebo interaction

Use the left mouse button to select an entity. Use the normal Gazebo view tools
to orbit, pan, zoom, move to an entity, or follow it. Avoid spawning or moving
robots during a measured run because that changes the experiment. If you want
to explore freely, use the warehouse playground instead:

```bash
make gazebo-gui
```

## Troubleshooting

- If `DISPLAY` is unset, start the command from the logged-in desktop terminal.
- If the XWayland check fails, confirm that Hyprland's XWayland support is
  enabled and that `xdpyinfo -display "$DISPLAY"` works as the current user.
- If the Gazebo pane is blank, confirm that the display-enabled container reports
  `OpenGL vendor string: Intel`. The verified presentation path uses Intel Mesa
  for Gazebo rendering and exposes the RTX 3050 Ti only to CUDA inference.
- Do not set `LIBGL_ALWAYS_SOFTWARE=1`; Ogre2/EGL software rendering was tested
  and crashed on this configuration.
- The optional OGRE1 GUI engine was tested and did not create usable windows on
  this stack. The supported presentation path is Intel OpenGL/EGL with Gazebo's
  OGRE2 engine and NVIDIA CUDA for YOLOv8n.
- Gazebo Transport is pinned to `GZ_IP=127.0.0.1` because every demonstration
  process runs on this laptop. This avoids multicast-discovery failures after
  the host upgrade.
- Stop a live project simulation with `bash infrastructure/dev/stop_simulation.sh`.
- A failed or interrupted presentation run remains separate from frozen gate
  evidence. Read its timestamped JSON summary before quoting any metric.

## Warehouse mission evidence

Run the repeated headless matrix with `make warehouse-mission-gate`. It enforces
the pair-first rule, then runs the three-follower mission three times while
recording CPU, RAM, GPU, VRAM, real-time factor, spacing RMSE, tracking fraction,
loading-station error, inference latency, command bounds, and collision samples.
Its results are separate from the original Gate 7 freeze.

Run the mapped repeatability matrix with `make warehouse-nav-mission-gate`.
It first runs one leader and one follower, then permits three repetitions with
all three followers. The final summary is
`work/ros2_ws/results/warehouse_nav_evidence/summary.json`.

## Why Hybrid-A* instead of RRT-Connect

RRT-Connect is a bidirectional sampling-based planner that is especially useful
in high-dimensional configuration spaces. It is not automatically the best
planner for every mobile-robot problem. This warehouse provides a known
two-dimensional occupancy map, and the leader is a differential-drive robot
with a minimum turning radius. Nav2 Smac Hybrid-A* directly searches position
and heading, accounts for footprint costs, and produces forward-only paths with
curvature constraints. That makes its output easier for the convoy to follow
through aisles than a raw point-to-point sampling tree.

The roles are deliberately separated:

- AMCL estimates the leader pose from the static map, wheel odometry, and LiDAR.
- Smac Hybrid-A* creates the global path between mission waypoints.
- Regulated Pure Pursuit converts that path into bounded leader commands and
  reduces speed near curvature and obstacles.
- Followers do not receive the map, LiDAR, path, or leader ground truth. Each
  follower uses its own RGB measurement and local wheel odometry.

The map contains three rows of shelves, a receiving/loading dock, a separate
dispatch/drop-off dock, perimeter walls, and cross-aisle turns. A four-second
pause at each navigation waypoint makes the stop behavior visible and gives the
formation time to settle. Those pauses model mission events only; they are not
measured material-handling throughput.

## Evidence boundary

The recorded videos are presentation artifacts. The repeated headless matrices
under `work/ros2_ws/results/pair_gate/`, `chain_gate/`, `disturbance_gate/`, and
`timing_gate/` remain the primary scientific evidence. A successful live video
does not replace repeated trials, and a GUI-loaded run is not used to rewrite
the frozen results.
