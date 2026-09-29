# Containerized Environment Setup

## Purpose

The Docker image is the canonical ROS 2 Jazzy and Gazebo Harmonic environment. The host's partial ROS installation is not used as project evidence. Docker improves reproducibility but does not replace recorded version, timing, and hardware checks. The image deliberately remains based on Ubuntu Noble even though the host now runs Ubuntu Resolute.

## Current host condition

The target host runs Ubuntu 26.04.1 LTS (Resolute) with kernel 7.0.0-34-generic. It has Docker Engine 29.8.1, Docker Compose 5.1.2, NVIDIA driver 595.91.07, and an RTX 3050 Ti with 4096 MiB VRAM. Docker's APT source uses the Resolute suite, and the pre-migration source file is retained under `/var/backups/`.

The host contains part of ROS 2 Lyrical, including `/opt/ros/lyrical/setup.zsh`, but the host `ros2` and `gz` commands are not available. Lyrical and Gazebo Jetty are therefore neither the implementation environment nor verified project evidence. The stale Jazzy startup lines were removed from the user's shell configuration, with a dated backup retained, so ordinary host terminals no longer try to source a missing distribution.

## Verified outcome

On September 29, 2026, after the host upgrade, the complete environment gate passed again. The container provided ROS 2 Jazzy, Gazebo Sim 8.15.0, and `ros_gz`. Four packages built, all 19 ROS package tests passed, both namespace probes passed, and the camera bridge delivered 15 timestamped 640×480 RGB images. All seven toy-simulation tests also passed. The GPU profile ran a CUDA tensor operation with PyTorch 2.9.1 on the RTX 3050 Ti. Ultralytics 8.4.165 is installed for the separately approved detector gate, but no YOLO accuracy or timing result is claimed yet.

The GPU-profile log contained EGL fallback warnings. Therefore, GPU passthrough is verified, but hardware-accelerated Gazebo rendering is not yet a measured claim.

## One-time Docker access decision

Membership in the `docker` group provides root-equivalent control through the Docker daemon. Use one of these approaches:

1. Run project commands with `sudo`, for example `make DOCKER='sudo docker' container-build`.
2. After accepting the security implication, add the development user to the Docker group and sign out and back in:

   ```bash
   sudo usermod -aG docker "$USER"
   ```

The project does not add this membership automatically.

## Optional NVIDIA container runtime

The CPU/software-rendering path is the default. To enable the approved GPU profile, review and run:

```bash
sudo bash infrastructure/docker/setup_nvidia_runtime.sh
```

The script installs NVIDIA Container Toolkit from NVIDIA's stable repository, backs up an existing Docker daemon configuration to `/etc/docker/daemon.json.ee616-backup`, configures the NVIDIA runtime, and restarts Docker.

Verify GPU access:

```bash
sudo docker run --rm --gpus all ubuntu nvidia-smi
```

## Build and validate

From the repository root:

```bash
make container-config
make container-build
make environment-check
```

After NVIDIA runtime setup, run the complete gate through the GPU profile:

```bash
make environment-check-gpu
```

If Docker group access is not enabled, use:

```bash
make DOCKER='sudo docker' container-config
make DOCKER='sudo docker' container-build
make DOCKER='sudo docker' environment-check
```

The check performs a `colcon` build and test, runs two namespace probes, launches a headless Gazebo camera world, bridges the image into ROS 2, and writes machine-readable evidence under `work/ros2_ws/results/environment_gate/`.

Open a development shell with `make container-shell`. Use `make gpu-shell` for an interactive GPU-profile shell.

## VS Code and graphical Gazebo

Start VS Code from a terminal in the logged-in Ubuntu desktop session so that `DISPLAY` and `XAUTHORITY` are available:

```bash
cd /home/justneeraj/Documents/MS_sem3/GRAD_PROJECT
code .
```

Select **Dev Containers: Reopen in Container**. The initialization script copies the current X11 authorization into an ignored temporary file and mounts only that file and the X11 socket into the container. It does not use unrestricted `xhost` access.

Inside VS Code, run the `EE616: Start simulation workspace` task. To test the GUI without VS Code, run:

```bash
make gazebo-gui
```

The GUI playground is a development and learning tool. It is not camera-accuracy or follower-control evidence. Detailed usage is in [`docs/DEVELOPER_WORKFLOW.md`](DEVELOPER_WORKFLOW.md).

## Generated files

The ROS `build/`, `install/`, and `log/` directories are local products and are excluded from Git. Machine-readable JSON summaries are retained as evidence. Large transient logs are excluded.

## Rollback

The repository foundation can be removed by reverting its Git commit. Host NVIDIA runtime rollback must be reviewed before execution. Restore `/etc/docker/daemon.json.ee616-backup` if it was created, remove the toolkit packages only after confirming no other project uses them, and restart Docker.
