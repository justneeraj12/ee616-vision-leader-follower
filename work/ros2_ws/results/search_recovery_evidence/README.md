# Bounded SEARCH Recovery Evidence

This directory is the accepted post-freeze evidence for the optional mapped-
mission `SEARCH` and `REACQUIRE` extension. It does not replace the frozen
Gate 1--7 evidence. It tests whether a follower can stop, perform a bounded
visual scan, confirm its predecessor, and resume without using Gazebo truth in
perception, estimation, supervision, or control.

## Result

The aggregate verdict is `pass_with_metric_limits`:

- 10 of 10 routes completed: one controlled pair blackout plus nine repeated
  mapped missions;
- zero sampled follower or warehouse-obstacle collisions;
- the controlled blackout entered `SEARCH` and `REACQUIRE`, commanded zero
  forward speed during search, and stayed within the 0.20 rad/s search-yaw
  bound;
- all three validated-pair repetitions passed every unchanged evaluator check;
- all three leader-command-dropout repetitions commanded zero leader output
  for all 180 of 180 observed fault samples; and
- all mapped followers remained below the unchanged 0.30 m transport-spacing
  RMSE limit.

Four of nine mapped runs passed every strict evaluator check. The other five
completed their route and passed every check except one or more followers fell
below the unchanged 90% `TRACK`-fraction threshold. The minimum observed values
were 89.01% in the nominal chain and 83.15% in the dropout chain. Time in
`SEARCH` and `REACQUIRE` is intentionally not counted as `TRACK`. The threshold
was not changed after observing the runs.

## Matrix

| Group | Runs | Strict pass | Route complete | Maximum spacing RMSE | Minimum TRACK fraction |
|---|---:|---:|---:|---:|---:|
| Controlled pair blackout | 1 | 1 | 1 | 0.1535 m | 91.00% |
| Nominal pair | 3 | 3 | 3 | 0.0953 m | 95.24% |
| Nominal three-follower chain | 3 | 1 | 3 | 0.1317 m | 89.01% |
| Three-follower leader dropout | 3 | 0 | 3 | 0.1189 m | 83.15% |

The mapped missions recorded 198 `SEARCH` samples and 131 `REACQUIRE`
samples. The controlled blackout recorded three `SEARCH` and two `REACQUIRE`
samples. Sample counts are evaluator samples, not independent trials.

## Recovery bounds

- zero commanded linear speed during `SEARCH`;
- maximum absolute search yaw command: 0.20 rad/s;
- scan envelope: plus or minus 60 degrees from the stopped heading;
- three range-consistent detections required;
- maximum candidate change from predicted range: 1.25 m;
- 0.50-second zero-command `REACQUIRE` hold; and
- 18-second hard search timeout followed by latched `SAFE_STOP`.

The convoy governor holds the leader while any follower is in `SAFE_STOP`,
`SEARCH`, or `REACQUIRE`. This is deterministic research behavior, not a
safety-rated stop or person-safety system.

## Resource interpretation

`component_resources.json` contains process-attributed measurements sampled
during the complete ten-run matrix. CPU values may exceed 100% because Linux
reports one fully used logical CPU as 100%. The three-follower perception and
control group contains six Python processes and reached 4577.6 MiB aggregate
resident memory. Resident-memory group totals include shared pages and must not
be added together as independent physical-memory use.

## Files and reproduction

- `aggregate_summary.json`: machine-readable gate result;
- `component_resources.csv` and `.json`: sampled component resources;
- each group directory: synchronized sample CSVs and evaluator summaries; and
- `SHA256SUMS`: integrity hashes.

From the project root, repeat the gate with:

```bash
make search-recovery-gate
```

The runner refuses to overwrite this directory. Move it deliberately before a
repeat. Development failures that motivated the final bounds are retained in
`../search_recovery_development/` and are not accepted results.

Environment recorded on 2026-11-09: Ubuntu host kernel 7.0.0-38, Intel
Core i5-12450H (12 logical CPUs), NVIDIA GeForce RTX 3050 Ti Laptop GPU
(4096 MiB), Docker Engine 29.9.0, ROS 2 Jazzy and Gazebo Harmonic in the project
container.
