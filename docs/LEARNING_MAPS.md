# Project Learning Maps

These maps are study aids. They show responsibility and evidence flow without claiming that planned components are already implemented.

## Project mind map

```mermaid
mindmap
  root((EE 616 convoy project))
    Problem
      Move warehouse material
      Avoid mechanically connected trailers
      Followers use local sensing
    Leader
      Owns route
      Initial deterministic path
      Later Smac 2D A-star candidate
    Followers
      Forward RGB camera
      Local wheel odometry
      Track immediate predecessor
    Perception
      Detect rear visual target
      YOLOv8n is a proposal
      Calculate range and bearing
    Estimation
      Kalman filter or EKF
      State and covariance
    Control
      Bounded linear speed
      Bounded angular speed
      Maintain requested gap
    Supervision
      TRACK
      PREDICT
      SAFE STOP
    Evaluation
      Synchronized logs
      Evaluation-only ground truth
      Error and timing metrics
    Evidence
      Toy baseline complete
      Environment gate complete
      Camera accuracy next
      Pair control later
```

## Runtime responsibility map

```mermaid
flowchart LR
    mission[Warehouse mission] --> planner[Leader route planner]
    planner --> leader[Leader controller]

    leader -->|rear visual target| camera1[Follower 1 camera]
    camera1 --> detect1[Detection]
    detect1 --> measure1[Range and bearing]
    odom1[Local odometry] --> estimate1[Relative-state estimator]
    measure1 --> estimate1
    estimate1 --> supervisor1[TRACK / PREDICT / SAFE STOP]
    supervisor1 --> control1[Bounded follower control]

    control1 --> follower1[Follower 1 motion]
    follower1 -->|rear visual target| camera2[Follower 2 camera]

    truth[Gazebo ground truth] -. evaluation only .-> evaluator[Logger and evaluator]
    measure1 -. measured data .-> evaluator
    estimate1 -. estimate and covariance .-> evaluator
    control1 -. commands .-> evaluator
```

The dotted ground-truth connection ends at the evaluator. It must never connect to detection, estimation, supervision, or control.

## Development-session map

```mermaid
flowchart TD
    host[Ubuntu desktop] --> vscode[VS Code]
    vscode --> container[ROS 2 Jazzy Dev Container]
    container --> build[colcon build and test]
    container --> launch[ROS 2 launch]
    launch --> gazebo[Gazebo Harmonic GUI and server]
    launch --> bridge[ros_gz bridge]
    gazebo --> gz_topic[Gazebo camera topic]
    gz_topic --> bridge
    bridge --> ros_topic[ROS image topic]
    ros_topic --> inspector[ROS learning terminal]
    ros_topic --> evidence[Explicit experiment logger]
```

## Evidence ladder

```mermaid
flowchart LR
    gate1[Gate 1<br/>Environment] --> gate2[Gate 2<br/>Camera measurement]
    gate2 --> gate3[Gate 3<br/>One pair]
    gate3 --> gate4[Gate 4<br/>Incremental chain]
    gate4 --> gate5[Gate 5<br/>Disturbances]
    gate5 --> gate6[Gate 6<br/>Resource tests]
    gate6 --> gate7[Gate 7<br/>Frozen package]
```

Each gate supports only the next bounded claim. A later demonstration cannot repair missing evidence from an earlier gate.
