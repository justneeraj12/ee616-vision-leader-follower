# Convoy-governance development evidence

This retained development run began with three passing one-follower repetitions
on the sparse layout and wide route. The next standard-layout pair run lost
visual continuity during the final route leg. The follower entered `SAFE_STOP`,
the convoy governor held the leader, and Nav2 eventually reported failure to
make progress after one bounded retry. The evaluator recorded zero robot or
mapped-obstacle collision samples.

The matrix was intentionally stopped after this result. It is not an accepted
experiment matrix. The final gate therefore validates the pair and incremental
chain on the same sparse/wide configuration and retains the standard-layout
pair only as a diagnostic boundary. The resource files in this directory cover
this partial development window only.
