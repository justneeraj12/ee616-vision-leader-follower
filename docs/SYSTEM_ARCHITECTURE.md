# System Architecture

## Research boundary

The project evaluates vision-based predecessor following for warehouse material transport. The validated leader-follower pair is the minimum scientific unit. A longer chain is added only after the pair passes its measurement and closed-loop tests.

## Robot roles

### Leader

The research leader follows a deterministic waypoint route. It provides repeatable motion and exposes a known visual target on its rear for Follower 1. The initial leader does not require a navigation camera or LiDAR because autonomous leader navigation is not the first research variable.

A later warehouse demonstration may add a 2-D LiDAR, wheel odometry, an IMU, and Nav2 to the leader if the core follower evidence and schedule support that extension. Those sensors would serve leader localization and route navigation.

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

Safety-rated obstacle and person protection is separate from formation coordination. A future safety sensor must not be described as evidence that the formation controller is safe or certified.

## ROS 2 package plan

| Package | Responsibility | Gate |
|---|---|---:|
| `ee616_bringup` | Launch, namespace, and environment checks | 1 |
| `ee616_simulation` | Gazebo worlds, robot spawning, and bridges | 1 onward |
| `ee616_description` | Robot URDF/SDF and sensor mounting | 2 |
| `ee616_perception` | Predecessor detection and range/bearing measurements | 2 |
| `ee616_estimation` | Relative-state estimation | 3 |
| `ee616_control` | Bounded formation commands | 3 |
| `ee616_supervisor` | `TRACK`, `PREDICT`, and `SAFE STOP` transitions | 3 |
| `ee616_evaluation` | Synchronized logging and evaluation-only ground truth | 2 onward |

Only the first two packages are created during the environment gate. Later packages require their own approved implementation stages.

## Ground-truth separation

Gazebo ground truth may enter `ee616_evaluation`. It must not enter perception, estimation, supervision, or control. Evaluation topics and data files must be named clearly so that this boundary can be audited.

## Initial performance strategy

- Run recorded experiments headlessly.
- Use simple visual and collision geometry.
- Begin with one 640 by 480 RGB camera at 15 Hz.
- Bridge only required topics.
- Separate physics, odometry, controller, camera, and logging rates.
- Record CPU, RAM, GPU, VRAM, real-time factor, and dropped images.
- Increase warehouse size and follower count only after measuring the preceding configuration.
