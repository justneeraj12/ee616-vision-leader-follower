# Convoy-governance development evidence

This directory retains two incomplete development matrices. Neither directory
is accepted experiment evidence.

- `standard_pair_attempt/` contains three passing sparse/wide pair runs and a
  failed standard-map pair run. The target left the camera view during the
  final route leg; the follower stopped and Nav2 later reported no progress.
- `predict_caution_attempt/` contains three passing sparse/wide pair runs and a
  failed three-follower sparse/wide run. Slowing, but not stopping, the leader
  while a follower was in `PREDICT` allowed visual loss to grow into
  `SAFE_STOP` during the final turn.
The failed runs recorded zero robot and mapped-obstacle collision samples. The
final policy uses reduced-speed caution during bounded `PREDICT` and a hard
leader hold for `SAFE_STOP`, stale follower health, or command dropout. The
final pair-first matrix is stored in the separate
`convoy_governance_evidence/` directory.
