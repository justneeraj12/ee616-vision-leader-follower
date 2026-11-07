# System Architecture

## Research boundary

The project evaluates vision-based predecessor following for warehouse material transport. The validated leader-follower pair is the minimum scientific unit. A longer chain is added only after the pair passes its measurement and closed-loop tests.

## Robot roles

### Leader

The controlled pair and chain gates use a deterministic leader route. This
keeps follower perception and control as the measured variables.

The mapped warehouse mission gives the leader route ownership through a static
occupancy map, wheel odometry, a simulated 360-degree LiDAR, AMCL localization,
Nav2 Smac Hybrid-A* planning, and Regulated Pure Pursuit control. These leader
inputs are not forwarded to any follower. The leader exposes the same rear
visual target for Follower 1 in both modes. In the revised mapped mission, Nav2
commands pass through a convoy governor before reaching the leader.

### Followers

Each follower is independently driven. Its formation layer uses:

- one forward RGB camera;
- local wheel odometry;
- predecessor detection;
- relative range and bearing measurement;
- a Kalman filter or EKF;
- bounded linear and angular control; and
- explicit `TRACK`, `PREDICT`, and `SAFE STOP` states.

Follower 1 tracks the leader. Follower 2 tracks Follower 1. Each later follower tracks its immediate predecessor. Every robot that has a follower behind it exposes the same rear visual target.

The revised mapped warehouse robot adds matching left, right, and front target
faces and uses a 120-degree forward RGB camera. The known target height remains
0.90 m, so the same pinhole height relationship applies with the configured
camera focal length.

The convoy governor uses only follower `TRACK`, `PREDICT`, and `SAFE_STOP`
states, estimator bearing and age, telemetry freshness, and the leader's Nav2
command. It reduces leader speed during turns or bounded `PREDICT`, and it
holds the leader for `SAFE_STOP`, stale follower health, or a stale leader
navigation command. Stable `TRACK` is required before resuming. This is
supervisory coordination, not follower localization or route data.

Safety-rated obstacle and person protection is separate from formation coordination. A future safety sensor must not be described as evidence that the formation controller is safe or certified.

## Current ROS 2 packages

| Package | Responsibility |
|---|---|
| `ee616_bringup` | Namespace and environment probes |
| `ee616_simulation` | Gazebo worlds, robot models, sensors, and ROS bridges |
| `ee616_perception` | Fixed-target baseline and YOLOv8n range/bearing measurements |
| `ee616_control` | Relative EKF, follower supervisor, bounded controller, convoy governor, leader mission, and Nav2 coordination |
| `ee616_evaluation` | Synchronized logging, metrics, plots, and evaluation-only Gazebo ground truth |
| `ee616_dashboard` | Validated experiment selection and read-only live telemetry |

Robot descriptions are generated with the simulation assets. Estimation and
supervision remain separate Python components inside `ee616_control`; they were
not split into extra ROS packages because the repeated follower node owns one
coherent estimator-supervisor-controller pipeline.

## Ground-truth separation

Gazebo ground truth may enter `ee616_evaluation`. It must not enter perception, estimation, supervision, or control. Evaluation topics and data files must be named clearly so that this boundary can be audited.

The browser dashboard receives estimator, governor, and command telemetry. Its live error
plot uses estimated range, not Gazebo truth. It can start or stop a complete
experiment process, but it does not publish velocity commands into a running
robot graph. The route drawing is schematic.

## Initial performance strategy

- Run recorded experiments headlessly.
- Use simple visual and collision geometry.
- Begin with one 640 by 480 RGB camera at 15 Hz.
- Bridge only required topics.
- Separate physics, odometry, controller, camera, and logging rates.
- Record CPU, RAM, GPU, VRAM, real-time factor, and dropped images.
- Increase warehouse size and follower count only after measuring the preceding configuration.
