# Mapped Warehouse Mission Development Record

This directory retains unsuccessful development evidence rather than hiding it.

`repeatability_target_switch_20261023/` records a failed repeatability attempt.
During a tight turn, Follower 2 temporarily lost its predecessor and selected a
farther robot with the same visual target. The resulting compression produced
collision samples, so this run was rejected. The correction was to select the
largest target-class image box, reject measurements beyond the declared local
tracking envelope, increase the EKF innovation gate only for this turning
mission, and slow forward motion at large bearing error. The corrected pair-first
matrix is retained separately under `warehouse_nav_evidence/`.

`time_contaminated_tuning_20261023/`, when present, is an invalid interrupted
tuning attempt. A previous container continued publishing simulation time, so
the partial result was not accepted. The final runner isolates both
`ROS_DOMAIN_ID` and `GZ_PARTITION` to prevent cross-run contamination.

Neither directory is accepted evidence. They are retained for traceability.
