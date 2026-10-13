# Faculty Review Overview

## Project identification

- Student: Neeraj Kumar Kanchani
- Faculty reviewer: Professor Masudul Imtiaz
- Course: EE 616-57, section 9189, four credits
- Project: Vision-based leader-follower coordination for warehouse material transport
- Current stage: Completed ROS 2 and Gazebo simulation package awaiting faculty feedback

## Project question

How accurately and reliably can an independently driven follower maintain a
requested distance from the robot directly ahead using a forward RGB camera and
local wheel odometry?

The project uses predecessor following:

- Follower 1 observes the leader.
- Follower 2 observes Follower 1.
- Every later follower observes its immediate predecessor.

The leader owns the route. The followers do not receive the leader route.

## Implemented solution

Each follower runs the same pipeline inside an isolated ROS 2 namespace:

1. Receive a forward RGB camera image.
2. Detect a known rear target with a synchronized YOLOv8n v3 model.
3. Convert the bounding box into relative range and bearing using calibrated
   monocular geometry and known target height.
4. Combine the measurement with local wheel odometry in a relative EKF.
5. Apply bounded range-and-bearing control.
6. Select `TRACK`, `PREDICT`, or `SAFE_STOP` according to measurement age.
7. Log synchronized behavior and timing data.

Gazebo position truth is read only by `ee616_evaluation`. It is not published to
perception, estimation, supervision, or control.

## Current leader behavior

The validated leader follows deterministic straight, gradual-turn, sharp-turn,
stop, and combined test profiles. This keeps follower experiments repeatable.
Autonomous global planning, SLAM, Nav2, A*, and RRT-Connect are not part of the
accepted implementation.

## Main parameters

| Parameter | Value |
|---|---:|
| Requested follower range | 1.50 m |
| RGB image | 640 by 480 pixels |
| Horizontal field of view | 70 degrees |
| Configured camera rate | 15 Hz |
| Controller rate | 20 Hz |
| Maximum forward command | 0.60 m/s |
| Maximum angular command | 0.80 rad/s |
| `TRACK` measurement age | At most 0.20 s |
| `PREDICT` measurement age | More than 0.20 s and at most 0.75 s |
| `SAFE_STOP` measurement age | More than 0.75 s or no initial measurement |

## Validation sequence and accepted results

| Stage | Accepted evidence | Interpretation boundary |
|---|---|---|
| Environment | ROS 2 Jazzy, Gazebo Sim 8.15.0, namespaced camera transport, and NVIDIA container access verified | One target laptop and canonical container |
| Camera measurement | YOLOv8n v3: 0.0323 m range RMSE, 0.1569 degree bearing MAE, 9.02 ms inference p95, and 100% valid over 1,620 fully visible sealed-gate samples | Controlled Gazebo scenes and a fixed-size target |
| One pair | Six runs passed; worst spacing RMSE was 0.0558 m straight and 0.1005 m during gradual turns | Nominal simulated pair behavior |
| Incremental chain | Twelve staged runs passed through three followers; worst F1--F3 RMSE was 0.1004, 0.0739, and 0.0523 m | Nominal matrix did not show rearward amplification |
| Controlled disturbances | Eighteen pair-first runs passed; combined F1--F3 worst RMSE was 0.1007, 0.1242, and 0.1403 m | Synthetic blackout and bounded yaw-command bias; this matrix showed rearward growth |
| Timing and resources | Worst p95 camera-to-measurement 23.09 ms, measurement-to-control 48.35 ms, detector inference 20.34 ms, control period 50.0 ms, minimum real-time factor 0.9996 | One-host simulation, not physical network or actuator timing |

All accepted pair, chain, disturbance, and timing matrices recorded zero collision
samples under the evaluator's center-distance threshold. This is not a person-safety
or industrial-certification result.

## Visual-loss behavior

- `TRACK`: a current camera measurement updates the EKF and bounded controller.
- `PREDICT`: the target is temporarily missing; the EKF predicts and forward speed
  is reduced to 55% of the normal bound.
- `SAFE_STOP`: the measurement is too old; linear and angular commands are zero.

The recovery demonstration uses a scheduled 1.3-second synthetic RGB blackout.
It demonstrates deterministic state transitions, not real dust, glare, lighting,
or physical occlusion.

## Demonstration material

| Material | Purpose |
|---|---|
| [Pair-turn video](deliverables/Neeraj_Kanchani_EE616_Gazebo_Pair_Turn_Demo.mp4) | One validated leader-follower pair during a gradual turn |
| [Three-follower video](deliverables/Neeraj_Kanchani_EE616_Gazebo_Three_Follower_Chain_Demo.mp4) | Predecessor-following topology with isolated follower controllers |
| [Recovery video](deliverables/Neeraj_Kanchani_EE616_Gazebo_Recovery_Demo.mp4) | Synthetic image loss, prediction, zero-command stop, and reacquisition |
| [Evidence walkthrough](deliverables/Neeraj_Kanchani_EE616_Gate7_Evidence_Walkthrough.mp4) | Short overview of the frozen Gate 1--7 evidence |
| [Technical handbook](deliverables/Neeraj_Kanchani_EE616_Project_Handbook_and_Simulation_User_Guide.pdf) | Detailed setup, algorithms, configuration, metrics, and troubleshooting |

Run a live presentation from the repository root:

```bash
make professor-demo PROFESSOR_DEMO=pair_turn
make professor-demo PROFESSOR_DEMO=chain_straight
make professor-demo PROFESSOR_DEMO=recovery
```

See [the professor demonstration guide](docs/PROFESSOR_DEMO_GUIDE.md) before a live
run. Presentation outputs are separate from the frozen experiment directories.

## Presentation screenshots

### Pair turn and three-follower chain

![Pair gradual turn in TRACK](deliverables/screenshots/pair_turn_track.png)

![Three-follower predecessor-following chain](deliverables/screenshots/three_follower_chain_track.png)

### Recovery sequence

![Synthetic blackout in PREDICT](deliverables/screenshots/recovery_predict.png)

![Synthetic blackout in SAFE STOP](deliverables/screenshots/recovery_safe_stop.png)

![Target returned and TRACK reacquired](deliverables/screenshots/recovery_reacquired.png)

These images are frames extracted from the recorded presentation videos. They
are visual aids, not separate experiment repetitions. Exact timestamps and
provenance are recorded in [the screenshot index](deliverables/screenshots/README.md).

## Code map

| Responsibility | Primary location |
|---|---|
| Gazebo robot and camera construction | `work/ros2_ws/src/ee616_simulation/ee616_simulation/pair_world.py` |
| YOLO target detection and range/bearing conversion | `work/ros2_ws/src/ee616_perception/ee616_perception/yolo_target.py` |
| Relative EKF and three-state supervisor | `work/ros2_ws/src/ee616_control/ee616_control/control_core.py` |
| ROS follower node | `work/ros2_ws/src/ee616_control/ee616_control/follower_node.py` |
| Deterministic leader route | `work/ros2_ws/src/ee616_control/ee616_control/leader_node.py` |
| Pair evaluation and truth boundary | `work/ros2_ws/src/ee616_evaluation/ee616_evaluation/pair_gate_evaluator.py` |
| Controlled disturbance proxy | `work/ros2_ws/src/ee616_evaluation/ee616_evaluation/disturbance_proxy.py` |
| Presentation launcher | `work/ros2_ws/src/ee616_evaluation/launch/professor_demo.launch.py` |

## Verified and unverified scope

Verified in the declared simulation configuration:

- Image-based measurement using YOLOv8n v3 and a known target.
- Closed-loop one-pair following.
- Incremental expansion through three followers.
- Deterministic visual-loss recovery states.
- Controlled turns, stopped-leader behavior, blackout, and actuator-command bias.
- One-laptop timing and resource use.
- Reproducible logs, summaries, checksums, and automated tests.

Not verified:

- Physical robots or real cameras.
- General target appearance or uncontrolled lighting.
- Wheel slip, physical motor faults, or real network timing.
- Safety-rated obstacle avoidance or person safety.
- Industrial certification or production readiness.
- General string stability.

## Requested faculty guidance

The simulation-stage project is complete enough for technical review. The next
stage should be selected after faculty feedback. Candidate directions are:

1. Increase perception realism with varied lighting, target appearance, and
   physical-camera effects.
2. Add autonomous leader navigation with a known-map ROS 2 Nav2 baseline.
3. Deepen the control analysis, including explicit string-stability questions.
4. Define a small physical pair experiment with a new safety and hardware scope.

No next direction is treated as approved until the faculty review and project-owner
decision are recorded.
