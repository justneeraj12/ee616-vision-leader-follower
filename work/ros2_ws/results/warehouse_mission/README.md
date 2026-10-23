# Warehouse Mission Evidence

This post-freeze experiment evaluates a staged material-transport mission in a
mid-size Gazebo warehouse. A leader-follower pair must pass before the runner
starts three leader-plus-three-follower repetitions.

Mission order:

1. leader and followers load in sequence at one station;
2. the loaded convoy follows a central aisle;
3. the leader performs a validated gradual aisle transition;
4. the convoy stops at the drop-off area; and
5. the visible cargo unloads in sequence.

Run it with:

```bash
make warehouse-mission-gate
```

`summary.json` is the aggregate decision record. Per-run JSON files contain
individual criteria and per-follower metrics. CSV files contain synchronized
samples. `resources.json` and `resource_samples.csv` record laptop load.
`warehouse_mission_metrics.png` is derived from the retained results, and
`SHA256SUMS` protects the JSON and CSV evidence.

The cargo lift is scripted visualization. The follower control path remains
camera plus local odometry, and Gazebo pose truth remains evaluation-only. This
experiment does not measure manipulation, airport or warehouse throughput,
physical robots, person safety, certification, or production readiness.
