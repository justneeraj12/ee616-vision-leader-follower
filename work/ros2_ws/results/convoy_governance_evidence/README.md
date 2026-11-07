# Convoy-governance gate evidence

This post-freeze matrix separates mission completion from failure containment.
The machine-readable acceptance result is `aggregate_summary.json`.

| Profile | Repetitions | Outcome |
|---|---:|---|
| Sparse/wide nominal pair | 3 | All passed; mean spacing RMSE 0.0860 m, minimum TRACK 95.8%, zero collision samples |
| Sparse/wide three-follower chain | 3 | All reached a contained governor `HOLD` after visual loss; zero collision samples; none completed the route |
| Sparse/wide pair with three-second command dropout | 3 | All passed; mean spacing RMSE 0.0959 m; all 180 fault samples had zero leader output; zero collision samples |

The chain rows are accepted containment evidence, not passing mission evidence.
The frozen nominal and mapped matrices remain the project's passing
three-follower mission evidence. These new runs show that the governor stops
the route owner when follower visual health is lost, but the current
forward-camera and zero-motion `SAFE_STOP` design cannot always reacquire a
predecessor that has already left the camera view.

`component_resources.csv` and `component_resources.json` attribute process CPU
and resident memory to leader navigation, follower perception/control, and
simulation/evaluation groups. They do not provide an all-independent-Nav2 cost
comparison. Gazebo pose truth was used only by `ee616_evaluation`.
