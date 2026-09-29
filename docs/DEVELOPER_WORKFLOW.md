# VS Code and Gazebo Development Workflow

## Purpose

This workflow keeps source code, ROS 2, Gazebo, experiment evidence, and report material in the single authorized project workspace. VS Code runs against the same Docker image used by the environment gate, so host ROS packages are not mixed with project evidence.

## First launch

1. Open a terminal from the logged-in Ubuntu desktop session.
2. Change to the project root:

   ```bash
   cd /home/justneeraj/Documents/MS_sem3/GRAD_PROJECT
   code .
   ```

3. In VS Code, select **Dev Containers: Reopen in Container**.
4. Wait for the image and ROS workspace build to finish.
5. Select **Terminal → Run Task → EE616: Start simulation workspace**.

The combined task builds the ROS workspace, starts the graphical warehouse playground, and opens a separate ROS learning shell. It does not run a follower experiment or create performance evidence.

## Daily workflow

Use these VS Code tasks:

| Task | Purpose |
|---|---|
| `EE616: Build ROS workspace` | Run `colcon build --symlink-install` |
| `EE616: Test ROS workspace` | Run the ROS package tests and show results |
| `EE616: Start simulation workspace` | Build, launch Gazebo, and open an inspection shell |
| `EE616: Launch selected scenario` | Choose and start one deterministic scenario |
| `EE616: Validate all controlled scenarios` | Check camera transport in all five templates |
| `EE616: Launch AWS warehouse benchmark world` | Open the optional imported warehouse |
| `EE616: Benchmark AWS warehouse headless` | Record fixed timing and resource evidence |
| `EE616: Open ROS learning shell` | Open a terminal with ROS 2 sourced |
| `EE616: Measure camera topic rate` | Measure `/smoke/camera/image` delivery rate |
| `EE616: Stop simulation` | Send a stop signal to playground processes |
| `EE616: Run seven toy tests` | Recheck the deterministic toy baseline |

Stop a running launch with `Ctrl+C` in its simulation terminal. The stop task is available if the terminal was closed first.

## Commands to learn

Run these in the ROS learning shell:

```bash
ros2 node list
ros2 topic list
ros2 topic info /smoke/camera/image
ros2 topic hz /smoke/camera/image
ros2 node info /camera_bridge
gz topic -l
gz sim --version
```

Use one command at a time and explain what it reports. A topic name alone is not evidence that the data are valid.

## Using the Gazebo playground

The development world is:

```text
work/ros2_ws/src/ee616_simulation/worlds/warehouse_playground.sdf
```

It contains a floor, six shelf blocks, a fixed camera rig, and a visual target. These are learning assets, not the final robot experiment.

In the Gazebo GUI:

- left-click an entity to select it;
- use the transform controls to translate or rotate selected objects;
- inspect models in the Entity Tree and Component Inspector;
- use the play and pause controls to control simulation time;
- display collisions when checking geometry; and
- save experimental copies with clear names instead of overwriting frozen evidence worlds.

Source-controlled changes should be made in the SDF file and reviewed in Git. A GUI-only edit is not reproducible until it is saved and committed.

## Selectable scenario templates

The controlled scenario definitions are under:

```text
work/ros2_ws/src/ee616_simulation/scenarios/
```

Use the VS Code `EE616: Launch selected scenario` task, or run one from the host:

```bash
make scenario-gui SCENARIO=narrow_aisle
make scenario-gui SCENARIO=partial_occlusion
```

Use `make scenario-validate` to check all five templates headlessly. Use `make aws-warehouse-gui` to open the optional AWS no-roof world and `make aws-benchmark` for its fixed headless resource test.

The scenario YAML files are the reproducible source. Generated SDF and manifest files are placed below `work/ros2_ws/log/generated_scenarios/`. See [the scenario matrix](SCENARIO_MATRIX.md) for each variable, benchmark values, provenance, and evidence boundaries.

## Display security

The Dev Container copies the current desktop session's X11 authorization file into an ignored temporary file before startup. It does not run `xhost +` and does not grant every local container access to the display.

If Gazebo does not open:

1. Confirm VS Code was started from the logged-in desktop session.
2. Confirm `DISPLAY` and `XAUTHORITY` are set in the host terminal.
3. Run `bash infrastructure/dev/prepare_xauthority.sh` on the host.
4. Rebuild or reopen the Dev Container.
5. Run the headless `make environment-check-gpu` to separate display problems from ROS/Gazebo problems.

## File ownership

The container uses the laptop user's numeric UID and GID. Generated ROS files should therefore remain editable from the host. Do not use `sudo` inside the project workspace to build ROS packages.

## Evidence boundary

Opening Gazebo, moving shelves, receiving an image topic, or observing a stable frame rate verifies development tooling only. It does not validate target detection, range, bearing, estimation, control, collision avoidance, or safety.
