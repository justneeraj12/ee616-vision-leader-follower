# SEARCH Recovery Development Evidence

These directories retain failed post-freeze development matrices. They are not
accepted project results. They explain why the final bounded-search design uses
an 18-second timeout, requires SEARCH before target confirmation, and applies a
1.25 m reacquisition range-consistency envelope.

## Attempt 1: search timeout too short

`attempt_01_progress_timeout/` used a 12-second search. The three pair runs
passed, but the first chain run did not complete. Follower 3 began SEARCH with
the true predecessor about 91 degrees off-axis and a stale EKF bearing pointing
the scan in the opposite direction. The scan reversed, but the timeout occurred
when the predecessor was still about 70 degrees off-axis, just beyond the
60-degree camera boundary. Nav2 later reported code 105 after the governor held
the leader. Sampled collisions remained zero.

## Attempt 2: reacquisition envelope too broad

`attempt_02_loose_reacquisition_gate/` used the longer search but allowed a
2.5 m range change during reacquisition. The pair stage passed. The first chain
run completed the route with zero sampled collisions, but Follower 2 accepted a
different visual panel at about 3.48 m when its prior predecessor estimate was
about 1.42 m. Chain spacing RMSE rose to 1.11 m for Follower 2 and 0.60 m for
Follower 3. The evaluator therefore failed the unchanged spacing and TRACK
checks.

## Correction

The accepted design does not confirm targets while waiting in SAFE_STOP.
Confirmation begins only after SEARCH starts, requires three consistent frames,
and rejects candidates more than 1.25 m from the predicted range. The search
continues to command zero linear speed, at most 0.20 rad/s yaw, and a bounded
plus-or-minus 60-degree scan. Gazebo pose truth was used only for post-run
diagnosis and never entered perception, estimation, supervision, or control.

## Attempt 3: startup state transition missing

`attempt_03_progress_window/` retained the tighter range gate, but a newly
introduced startup edge case left Follower 2 internally labeled SAFE_STOP after
its first valid measurement. The SAFE_STOP association guard then rejected
later frames before the control timer could establish TRACK. The governor held
the leader and Nav2 eventually reported code 105. This was not accepted as a
recovery or planner result. The correction explicitly enters TRACK when the
EKF is initialized from the first valid measurement and adds a regression test
for a second camera frame arriving before the first control step.
