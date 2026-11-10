# Configurable Experiment Console

## Purpose

The experiment console provides one local browser interface for the mapped
warehouse mission. It selects a bounded experiment profile, starts the existing
ROS 2 launch stack, displays live telemetry, and preserves the evaluator output.
It does not publish velocity commands or use Gazebo pose truth for control.

The console is a configuration and explanation tool. It is not a fleet manager
or a safety controller.

## Start the console

From the authorized project root, run:

```bash
./launchers/experiment_console.sh
```

The launcher builds the six ROS packages required by the console and mission,
then normally opens:

```text
http://127.0.0.1:8765
```

If the browser does not open automatically, enter that address manually. Keep
the terminal open while using the console. Press `Ctrl+C` in the terminal to
stop the console and any experiment that it started.

## Selectable options

| Option | Choices | Meaning |
|---|---|---|
| Followers | 1, 2, or 3 | Starts the same follower pipeline under isolated namespaces |
| Route profile | Wide, standard, or turn-dense stress | Changes the leader's validated waypoint list |
| Warehouse layout | Nine-shelf standard or six-shelf sparse | Regenerates the Gazebo world and Nav2 occupancy map |
| Gazebo view | On or off | Opens or suppresses the graphical client; control is unchanged |
| Scenario | Nominal or leader command dropout | Selects normal operation or a bounded three-second leader-command interruption |

Only predefined profiles are accepted. The HTTP service rejects unknown route,
map, and scenario names, follower counts outside 1--3, oversized requests, and a second start
request while an experiment is running. ROS launch arguments are assembled as
an argument list rather than a shell command.

## Live values

The top cards show the mission state, Nav2 planner and controller, convoy
governor mode, current and peak container memory, system load, GPU device,
utilization and memory, and current and peak process-attributed CPU and RAM.
The GPU card reads `nvidia-smi` from the display-enabled project container and displays a
diagnostic instead of a blank value when the device query is unavailable.

The governor is an explicit command proxy between Nav2 and the leader. It uses
follower supervisor state, estimator bearing, measurement age, and message
freshness. It does not subscribe to Gazebo poses. It reduces leader speed for a
turn or `PREDICT`, commands zero leader motion for `SAFE_STOP`, `SEARCH`,
`REACQUIRE`, or stale health, and requires a stable `TRACK` interval before
resuming.

Each follower row shows:

- `TRACK`, `PREDICT`, `SAFE_STOP`, `SEARCH`, or `REACQUIRE`;
- EKF estimated range and bearing;
- estimated spacing error relative to the requested 1.5 m separation;
- estimated RMSE accumulated during the current console run;
- measurement age;
- bounded linear and angular commands;
- YOLO inference time and detection confidence.

The live spacing graph uses the EKF estimate. It is not a ground-truth graph.
The separate `ee616_evaluation` process reads Gazebo pose truth and writes the
post-run CSV and JSON files without publishing truth to perception, estimation,
supervision, or control.

The **Export live snapshot** button downloads the current browser telemetry as
JSON. The scientific output is the evaluator CSV and JSON written below:

```text
work/ros2_ws/results/dashboard_runs/<timestamp>_<map>_<route>_<scenario>_<count>f/
```

These console runs are ignored by Git and do not change the frozen Gate 1--7
evidence.

After a run, the console separates the live record from the evaluator verdict:

- `PASS`: the route completed and all declared evaluator checks passed;
- `LIMITED`: the route completed, but one or more unchanged metric checks did
  not pass;
- `CONTAINED`: the route did not complete, but the governor held the convoy and
  sampled collisions remained zero; and
- `FAILED`: the run did not meet those conditions.

Process memory is the sum of resident memory reported by matching processes.
It is useful for attribution, but shared pages mean those group values must not
be added to the cgroup container-memory value as if they were independent.

## Route profiles and validation history

| Profile | Configuration | Result |
|---|---|---|
| Wide | One follower, three accepted recovery repetitions | All strictly passed: 0.0910 m mean spacing RMSE, at least 95.24% TRACK, zero collision samples |
| Wide | Three followers, three nominal repetitions | All routes completed with zero collision samples; one strict pass, two limited only by the 90% TRACK-fraction check |
| Wide + leader dropout | Three followers, three repetitions | All routes completed; 180 of 180 fault samples had zero leader output; all three limited only by one or more TRACK-fraction checks |
| Standard | Two followers, one initial run | Passed before the governor revision: 0.1405 m and 0.1276 m RMSE, zero collision samples |
| Standard | One revised governed pair | Failed diagnostic: visual continuity was lost on the final leg and the route did not complete |
| Turn-dense stress | One follower | Failed after repeated turns; the failure is retained as diagnostic evidence |

The turn-dense route is deliberately labeled as a stress profile. The pair
tracked the first straight aisle for 100% of its samples. TRACK fell to 83.8%
on the first cross-aisle turn, recovered to 99.7% on the next straight aisle,
and fell to 27.0% on the second cross-aisle turn. The follower then remained in
`SAFE_STOP` while the leader continued. The final leader segment was aborted by
Nav2's collision-ahead check. No evaluator robot or mapped-obstacle collision
sample occurred.

This negative result established that independent safe stopping was not
sufficient for mission continuity. The governance gate added a low-bandwidth
convoy governor, four visual target panels, and a 120-degree mapped-mission
camera. Its original incomplete chain runs remain retained development
evidence. The later bounded-search revision completed all six accepted
three-follower routes, but five runs remained below the unchanged 90% `TRACK`
fraction. Both the recovery and the remaining metric limit are reported.

## Post-run segment metrics

New evaluator summaries separate every `NAV_*` route leg and follower. Each
segment reports:

- spacing RMSE;
- peak absolute spacing error;
- TRACK fraction;
- PREDICT fraction;
- SAFE STOP fraction;
- SEARCH fraction; and
- REACQUIRE fraction.

The summary also reports each follower's total RMSE relative to Follower 1.
This makes rearward amplification measurable without claiming general string
stability.

## Interpretation limits

- The console uses a schematic route drawing, not Gazebo truth robot positions.
- Live RMSE is estimated RMSE. Quote the post-run evaluator result in technical
  material.
- The wide pair and the accepted nominal/dropout three-follower matrices have
  repeated evidence. Other console combinations do not become validated merely
  because they are selectable.
- The original turn-dense configuration failed. Do not imply that a later
  revision changes that historical result.
- A leader command-dropout experiment demonstrates bounded containment and
  recovery only. It is not autonomous leader replacement.
- Safety-rated sensing, physical robots, human traffic, and production safety
  remain outside the demonstrated evidence.
