# Gazebo Scenario Matrix

## Purpose

The project uses small, deterministic scenarios as the primary scientific environments. Each scenario changes one main condition while keeping the camera interface, target geometry, seed, and rendering settings traceable. This is more useful for measurement experiments than relying on one visually complex warehouse.

The AWS no-roof warehouse is a separate optional stress test. It checks whether a larger imported scene loads and runs on the target laptop. It is not the source of camera-accuracy or follower-control claims.

## Fixed scenario interface

All controlled scenarios inherit from `base.yaml` and use:

- deterministic seed `616`;
- `/smoke/camera/image` as the ROS image topic;
- 640 × 480 RGB images at a requested 15 Hz;
- a 70-degree horizontal field of view;
- the same red rectangular target dimensions;
- fixed lighting unless the experiment explicitly changes it; and
- generated SDF and JSON manifests identified by a configuration SHA-256 hash.

The current target and fixed camera are measurement-development assets. They are not yet a moving leader or follower.

## Controlled scenarios

| Scenario | Main condition | Current use | Future Gate 2 use |
|---|---|---|---|
| `camera_calibration` | Open scene | Camera transport check | Controlled range and bearing sweeps |
| `straight_aisle` | Symmetric shelf background | Camera transport check | Background sensitivity and nominal measurements |
| `right_angle_turn` | Cross aisle beside an L-shaped boundary | Camera transport check | Off-axis bearing and corner visibility |
| `narrow_aisle` | Close shelf structure on both sides | Camera transport check | Restricted-view and clutter sensitivity |
| `partial_occlusion` | Thin object obscuring part of the target | Camera transport check | Detection validity and later loss/reacquisition tests |

The checked-in validator received 30 timestamped 640 × 480 RGB frames in every scenario. This verifies configuration generation, Gazebo loading, bridging, and message transport only. It does not verify target detection or range and bearing accuracy.

## Running a controlled scenario

From the host project root:

```bash
make scenario-gui SCENARIO=straight_aisle
make scenario-gui SCENARIO=partial_occlusion
```

Inside the VS Code Dev Container, run `EE616: Launch selected scenario` and choose a scenario from the prompt. Use `Ctrl+C` in the simulation terminal when finished.

Run the repeatable headless transport check with:

```bash
docker compose run --rm dev bash /workspace/infrastructure/benchmarks/validate_scenarios.sh
```

Machine-readable results are written below `work/ros2_ws/results/scenario_validation/`. Launch logs are local diagnostic artifacts and are ignored by Git.

## Changing a scenario

Make reproducible changes in `work/ros2_ws/src/ee616_simulation/scenarios/`. Do not use a GUI-only edit as experiment evidence.

1. Copy the closest scenario YAML file.
2. Give it a lowercase underscore-separated name.
3. Change one primary condition where possible.
4. State the `variable_under_test` and `expected_visibility`.
5. Build the ROS workspace and run the scenario validator.
6. Record any new experiment acceptance criteria before collecting performance evidence.

The scenario loader permits one inheritance level and prevents the `extends` field from leaving the scenario directory.

## AWS no-roof warehouse

The optional imported scene is a pinned subset of the archived AWS RoboMaker Small Warehouse World. The original ROS 2 branch used Gazebo Classic. This repository instead vendors the no-roof world and models from a Jazzy/Harmonic conversion source at commit `a8ba1cea777799d51db58f759e4d2cfa2c81fd74`. The included source world is unchanged. The launch path creates a runtime copy and adds only the fixed benchmark camera and target.

Run it graphically:

```bash
make aws-warehouse-gui
```

Run the fixed headless benchmark:

```bash
make aws-benchmark
```

The September 28, 2026 benchmark passed with:

| Measurement | Result |
|---|---:|
| Camera samples | 150 of 150 |
| Camera receive rate | 15.19 Hz |
| Median real-time factor | 0.9999 |
| Fifth-percentile real-time factor | 0.9988 |
| Peak container memory | 364.7 MiB |
| CPU use | 47.9% of one core equivalent |
| Visible NVIDIA memory | 253 MiB |
| Peak reported GPU utilization | 19% |
| Fatal model or plugin errors | 0 |

The graphical world also opened in Gazebo Sim 8.15.0. Mesa, GLX, and EGL fallback warnings were present, so these results do not prove that Gazebo rendering used the NVIDIA GPU. The resource measurements include ROS and benchmark support processes. No image detector, follower estimator, controller, collision experiment, or safety test ran in this benchmark.

## Evidence boundary

The scenario system supports Gate 2 but does not complete it. Gate 2 still requires estimated range and bearing to be compared against evaluation-only Gazebo ground truth across a declared test matrix. Ground truth must remain outside detection, estimation, supervision, and control.
