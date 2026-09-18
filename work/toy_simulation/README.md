# Vision Only Leader Follower Toy Baseline

This package is the first reproducible evidence baseline for the EE 616 project. It simulates a leader and a unicycle follower in two dimensions, generates camera-like bounding-box measurements, estimates the leader state with a constant-velocity Kalman filter, and controls the follower with a bounded range-and-bearing controller.

## What this baseline establishes

- deterministic experiments from recorded seeds;
- monocular range and bearing derived from synthetic bounding-box geometry;
- prediction through short visual occlusions;
- explicit TRACK, PREDICT, and SAFE_STOP states;
- machine-readable trial data and summary metrics;
- figures suitable for an initial faculty discussion.

## What it does not establish

This is not a ROS 2 or Gazebo result. It does not use a learned detector, photorealistic images, wheel slip, network traffic, or GPU inference. Its purpose is to validate the experiment contract and expose controller or estimator problems before the Gazebo implementation begins.

## Run

The only runtime dependencies are NumPy and Pillow.

```bash
PYTHONPATH=src python -m toy_swarm.run --output results
python -m unittest discover -s tests -v
```

The run creates per-trial metrics, a representative time-series CSV, an aggregate JSON summary, and four PNG figures.

## Evidence contract

Each trial records the seed, scenario, ground-truth leader and follower states, measurement availability, estimated relative state, controller state, commands, and safety events. Proposed project thresholds are shown as references only; passing this toy model is not evidence that the later Gazebo or edge-inference system will pass.
