# EE 616 ROS 2 Workspace

This workspace contains the ROS 2 Jazzy and Gazebo Harmonic implementation for the project. The deterministic Python toy simulator remains separate under `work/toy_simulation/`.

The container is the canonical development environment. From the repository root:

```bash
make container-build
make environment-check
```

The environment check builds the workspace, tests two isolated namespaces, launches a minimal headless Gazebo camera world, bridges the image to ROS 2, and writes evidence to `results/environment_gate/`.

Current packages:

- `ee616_bringup`: environment probes and namespace smoke tests.
- `ee616_simulation`: the minimal Gazebo camera smoke-test world and bridge.

Later perception, estimation, control, supervisor, and evaluation packages require separate implementation approval. Gazebo ground truth must remain outside detection, estimation, supervision, and control.
