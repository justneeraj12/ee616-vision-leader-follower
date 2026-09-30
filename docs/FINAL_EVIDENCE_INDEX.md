# Final Evidence Index

## Purpose

This index identifies the frozen evidence for the EE 616 vision-based predecessor-following project. It separates verified simulation results from demonstrations, failed experiments, development checks, and unverified physical-world claims.

Project owner: Neeraj Kumar Kanchani  
Course: EE 616-57, section 9189, four credits  
Faculty reviewer: Professor Masudul Imtiaz  
Freeze date: September 30, 2026

## Claim boundary

The package supports a reproducible ROS 2 Jazzy and Gazebo Harmonic implementation and evaluation on one target laptop. It does not demonstrate physical robots, networked robots, wheel slip, safety-rated obstacle avoidance, person safety, industrial certification, or production readiness.

Gazebo pose truth is restricted to `ee616_evaluation`. It is not an input to detection, state estimation, supervision, or control.

## Gate index

| Gate | Question | Frozen result | Primary evidence |
|---|---|---|---|
| 1 | Does the canonical environment build and transport namespaced camera data? | Pass | `work/ros2_ws/results/environment_gate/summary.json` |
| 2a | Does deterministic camera geometry meet the fixed measurement limits? | Pass | `work/ros2_ws/results/camera_measurement_gate/summary.json` |
| 2b | Does learned image detection meet the sealed measurement limits? | v1 fail, v2 fail, v3 pass | `work/ros2_ws/results/yolo_measurement_gate*/summary.json` |
| 3 | Does one leader-follower pair close the loop under nominal straight and turn routes? | Pass, six runs | `work/ros2_ws/results/pair_gate/summary.json` |
| 4 | Does staged expansion to two and three followers pass the nominal matrix? | Pass, twelve runs | `work/ros2_ws/results/chain_gate/summary.json` |
| 5 | Does the pair-first disturbance matrix produce the required recovery behavior? | Pass, eighteen runs | `work/ros2_ws/results/disturbance_gate/summary.json` |
| 6 | Does the accepted three-follower scenario meet timing and laptop-resource limits? | Pass, three runs | `work/ros2_ws/results/timing_gate/summary.json` |
| 7 | Are the protocols, source, evidence, manual, and review package frozen and verifiable? | Verified by the Gate 7 checksum tool | `work/gate7_package/` |

## Accepted numerical results

### Environment

- ROS distribution: ROS 2 Jazzy.
- Simulator: Gazebo Sim 8.15.0 from the Harmonic family.
- Camera transport: 15 timestamped 640 by 480 RGB samples.
- Target GPU profile: NVIDIA RTX 3050 Ti Laptop GPU with 4,096 MiB visible VRAM.

### Camera measurement

- Deterministic red-target baseline: 0.0355 m range RMSE and 0.120 degrees bearing MAE over 1,620 full-visible samples.
- Synchronized YOLOv8n v3: 100% valid full-visible rate, 0.0323 m range RMSE, 0.1569 degrees bearing MAE, and 9.02 ms p95 inference latency over the sealed two-scene matrix.
- YOLOv8n v1 and v2 remain retained failed evidence and must not be described as successful detectors.

### Closed-loop pair and chain

- One pair: worst spacing RMSE was 0.0558 m for straight motion and 0.1005 m for gradual turns; zero evaluator collision samples.
- Three-follower nominal matrix: worst spacing RMSE was 0.1004 m, 0.0739 m, and 0.0523 m from Follower 1 through Follower 3; zero evaluator collision samples. Rearward amplification was not observed in this nominal matrix.
- Combined disturbance matrix: worst spacing RMSE was 0.1007 m, 0.1242 m, and 0.1403 m from Follower 1 through Follower 3; zero evaluator collision samples. This matrix showed rearward error growth.

### Recovery and timing

- Long synthetic RGB blackouts produced `PREDICT`, then `SAFE_STOP`, zero command during `SAFE_STOP`, and later `TRACK` reacquisition.
- The blackout is not physical occlusion. The yaw-command bias is not wheel slip or a motor fault.
- Gate 6 worst p95 values were 23.09 ms camera to measurement, 48.35 ms valid measurement to controller command, 2.89 ms controller command to post-proxy command, 20.34 ms detector inference, and 50.0 ms control period.
- Minimum measurement delivery ratio was 95.4%, and minimum real-time factor was 0.9996.
- Peak container memory was 3,584 MiB and peak visible GPU memory was 642 MiB.

## Toy baseline

The earlier deterministic two-dimensional toy simulator remains useful as preliminary design evidence. It contains 32 pair trials and an 86-second warehouse demonstration with three followers. It does not replace ROS 2 or Gazebo evidence.

## Reproduction commands

From the project root:

```bash
make environment-check-gpu
make pair-gate
make chain-gate
make disturbance-gate
make timing-gate
```

These commands overwrite their corresponding result directories. Preserve the frozen package before intentionally collecting a new experimental revision.

## Integrity verification

Run:

```bash
python3 work/gate7_package/verify_frozen_evidence.py
```

The verifier checks every frozen file against `work/gate7_package/FROZEN_SHA256SUMS` and checks that each accepted or retained-failure summary still has its recorded status.

## Interpretation rule

Every number used in a report or presentation must identify its experiment, source file, unit, sample or run count, calculation, and limitation. A successful simulation result is evidence about the declared simulation configuration only.
