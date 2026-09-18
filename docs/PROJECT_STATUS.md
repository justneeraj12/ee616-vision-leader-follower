# Project Status

Last updated: September 18, 2026

## Current state

The deterministic Python toy baseline is complete. It includes a single-pair experiment harness and a warehouse-maze demonstration with one leader and three independently controlled followers.

The current environment does not yet contain a verified complete ROS 2 Jazzy, Gazebo Harmonic, and inference runtime. No Gazebo performance result has been claimed.

## Verified evidence

- Seven automated toy-simulation tests pass.
- The multi-follower warehouse run is deterministic for its recorded seed.
- The nominal 86-second run completed seven path segments.
- The run recorded zero collision samples in the toy collision model.
- Spacing RMSE was 0.140 m, 0.164 m, and 0.200 m from Follower 1 through Follower 3.
- Faculty-facing DOCX and PDF reports have been rendered and visually checked.
- The eight-page initial technical explanation contains four traceable figures and has been rendered and visually checked page by page.
- A two-dimensional warehouse demonstration video is available in `deliverables/`.
- A private GitHub repository has been created at `https://github.com/justneeraj12/ee616-vision-leader-follower`.

## Evidence limitations

- Kinematic rather than Gazebo physics
- Idealized follower pose and camera-like measurements
- No learned image detector
- No ROS 2 timing or namespace audit
- No wheel slip, actuator dynamics, person traffic, or safety-rated obstacle system
- No physical robot validation or certification claim

## Current deliverables

- Initial technical explanation and preliminary figures in DOCX and PDF
- Industry application and system rationale in DOCX and PDF
- Initial toy simulation results in DOCX and PDF
- Multi-follower warehouse demonstration video
- Single-follower toy demonstration video
- Reproducible baseline ZIP packages

## Repository state

The project is maintained in the private GitHub repository `justneeraj12/ee616-vision-leader-follower`. The repository includes the governing documentation, source, automated tests, machine-readable evidence, report builders, and review deliverables. Internal render pages, temporary artifacts, and quality-check screenshots are excluded through `.gitignore`.

## Next proposed approval gate

Environment and reproducibility validation for ROS 2 Jazzy and Gazebo Harmonic, followed by a measurement-only camera experiment that compares estimated range and bearing with Gazebo ground truth.

## Two gates ahead

1. Integrate one leader and one follower with estimator, bounded controller, and TRACK, PREDICT, and SAFE STOP states.
2. Add followers one at a time and measure spacing-error propagation, corner behavior, minimum separation, and stopping behavior.

## Current blockers

- ROS 2 Jazzy and Gazebo Harmonic have not been verified as a complete working stack on the target machine.
- The final leader visual target and camera measurement model have not been selected through Gazebo evidence.
- Professor Imtiaz has not yet reviewed the latest application rationale and toy evidence package.
- The GitHub repository is private and has not been presented as a public release.
