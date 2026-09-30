# Decision Log

## D001 Application definition

Date: September 17, 2026

Decision: Define the industrial application as a flexible autonomous material-delivery convoy for warehouse and manufacturing aisles.

Reason: The application connects the research to established follow-me robots, tugger trains, autonomous mobile robot transport, replenishment, and post-pick workflows without claiming that the exact proposed system is already a standard product.

## D002 Sensor scope

Date: September 17, 2026

Decision: Use a forward RGB camera and local wheel odometry for the follower formation layer. Do not include ODIN-fire, LiDAR, or stereo fusion in the current research scope.

Reason: This gives the project a measurable research question that fits the semester and target computer while preserving perception, estimation, control, recovery, and edge-compute challenges.

## D003 Chain topology

Date: September 17, 2026

Decision: Use predecessor following. Follower 1 tracks the leader, and each later follower tracks the robot immediately ahead.

Reason: The local field of view remains practical as the convoy grows, and each follower can use the same interface. Error propagation must be measured before the convoy length is considered validated.

## D004 Safety boundary

Date: September 17, 2026

Decision: Treat vision-based formation coordination and industrial robot safety as separate layers.

Reason: A monocular following controller is not a complete safety system. Deployment would require independent safety-rated sensing, emergency stops, verified stopping behavior, site commissioning, and applicable standards compliance.

## D005 Evidence language

Date: September 17, 2026

Decision: Label the existing results as toy kinematic evidence, not ROS 2, Gazebo, physical robot, or production evidence.

Reason: The current simulator validates the experiment structure and exposes control behavior under simplified assumptions. Stronger claims would not be supported.

## D006 Project workspace

Date: September 18, 2026

Decision: Use `/home/justneeraj/Documents/MS_sem3/GRAD_PROJECT` as the main project workspace.

Reason: Reports, media, source, results, references, and documentation need one stable location.

## D007 Faculty technical explanation

Date: September 18, 2026

Decision: Consolidate the initial technical explanation and preliminary evidence into one faculty-review report with four traceable figures covering topology, camera geometry, recovery states, and recorded toy results.

Reason: The earlier reports contain useful material, but the technical explanation and evidence are distributed across separate packages. A consolidated report gives Professor Imtiaz one direct document to review without strengthening the claims beyond the recorded evidence.

## D008 Private GitHub repository

Date: September 18, 2026

Decision: Maintain the project in the private GitHub repository `justneeraj12/ee616-vision-leader-follower` and exclude internal render pages, temporary artifacts, and quality-check screenshots.

Reason: The repository should contain the files needed to understand, reproduce, and review the project without publishing unnecessary build residue or presenting the work as a public release.

## D009 Repository presentation and continuous integration

Date: September 18, 2026

Decision: Structure the repository landing page after Neeraj's recent research and systems repositories, with badges, a candid status boundary, verified evidence, architecture, quickstart instructions, a validation roadmap, scope limitations, contribution guidance, citation metadata, and automated testing on supported Python versions.

Reason: The repository should be understandable to a faculty reviewer or portfolio reviewer without requiring them to open every report. Automated tests and explicit evidence boundaries make the current condition reproducible without presenting the toy baseline as a production-ready robot.

## D010 Faculty report format and writing style

Date: September 18, 2026

Decision: Use the IEEEtran LaTeX class in single-column mode for the separate technical report. Use simple formal English, short sentences, direct first-person statements, and explicit evidence limitations. Preserve the previously submitted report without modification.

Reason: The report should be easy for Neeraj to read, explain, revise, and defend during faculty review while retaining a recognized engineering-paper structure.

## D011 Canonical container environment

Date: September 28, 2026

Decision: Use a Docker image based on the official ROS 2 Jazzy Ubuntu Noble image as the canonical ROS 2 Jazzy and Gazebo Harmonic environment. Default experiment execution is headless with software rendering available as a fallback. GPU execution is an optional measured profile.

Reason: The host contains an incomplete ROS 2 installation. A versioned container reduces host coupling, records dependencies, supports repeatable clean builds, and allows the CPU and GPU paths to be compared without creating a second project workspace.

## D012 Leader sensing boundary

Date: September 28, 2026

Decision: Use a deterministic waypoint-driven leader for the initial measurement and pair-control experiments. The leader exposes a rear visual target but does not require a navigation camera or LiDAR at this gate. A later warehouse demonstration may add 2-D LiDAR, wheel odometry, an IMU, and Nav2 if the core evidence and schedule support it.

Reason: Leader autonomous navigation is not the first research variable. Controlled leader motion makes follower measurement, estimation, and control errors easier to isolate. The later sensor extension remains separate from the follower formation inputs.

## D013 Integrated development workflow

Date: September 28, 2026

Decision: Use the existing Docker image through a VS Code Dev Container as the standard interactive development workflow. Copy only the current X11 authorization record into a temporary ignored file for Gazebo GUI access. Keep the warehouse playground separate from frozen experiment evidence.

Reason: One integrated environment reduces host-version errors and keeps terminals, builds, tests, ROS inspection, and Gazebo controls together. The restricted display credential avoids unrestricted `xhost` permissions. A development playground supports learning without turning an editable scene into scientific evidence.

## D014 Controlled scenario matrix and optional AWS stress test

Date: September 28, 2026

Decision: Use small deterministic YAML scenarios as the primary Gate 2 measurement environments. Keep the pinned AWS no-roof warehouse as an optional visual and resource stress test, not as the primary scientific environment.

Reason: Controlled scenes isolate range, bearing, background, aisle, corner, and visibility conditions. The larger imported warehouse demonstrates compatibility with the target laptop but would make early measurement errors harder to diagnose. Its archived upstream status and Gazebo migration history also require explicit provenance and a fixed local subset.

## D015 Camera geometry baseline before learned detection

Date: September 29, 2026

Decision: Validate the range and bearing geometry first with a deterministic fixed-size red target and a pixel-based detector. Keep Gazebo pose access inside a separate evaluation package. Evaluate YOLOv8n later against the same frozen matrix before using it in the follower pipeline.

Reason: This separates camera calibration and geometry error from learned-detector error. The ground-truth boundary can be tested directly, and a later detector comparison uses the same ranges, bearings, scenes, metrics, and acceptance thresholds.

## D016 Public AGPL repository

Date: September 29, 2026

Decision: Publish the existing GitHub repository and its full history under AGPL-3.0-only for original project software and documentation. Preserve the MIT terms of the pinned AWS warehouse assets and identify external reference documents as third-party material outside the repository-wide license.

Reason: The project owner approved public release after reviewing that the history contains faculty-facing deliverables, internal project records, personal academic context, and external reference files. Ultralytics' official guidance identifies its YOLO software and models as AGPL-3.0 unless a separate enterprise license applies. A public AGPL project therefore supports the approved YOLOv8n evaluation without presenting third-party material as project-owned content.

## D017 Host upgrade compatibility

Date: September 29, 2026

Decision: Keep the canonical Ubuntu Noble container with ROS 2 Jazzy and Gazebo Harmonic after the laptop host upgrade to Ubuntu 26.04.1 LTS. Do not migrate the project to the host's partial ROS 2 Lyrical installation or to Gazebo Jetty during the current validation sequence.

Reason: The approved experiments and evidence already target Jazzy and Harmonic. The versioned container passed the full ROS, namespace, camera, toy-test, and CUDA checks after the host upgrade. Changing distributions now would add migration risk without improving the next scientific gate.

## D018 YOLO target and dataset separation

Date: September 29, 2026

Decision: Detect the same 0.70 m by 0.90 m solid rear target used by the fixed-pixel baseline, use `predecessor_target` as the only learned class, separate training, validation, and test data by complete Gazebo scene, and keep the A012 camera-calibration and straight-aisle scenes out of all training data.

Reason: A known target height preserves the approved monocular range equation. Reusing its geometry supports a fair detector comparison. Scene-level separation reduces background leakage, and retaining the unchanged A012 scenes provides an independent final measurement gate.

## D019 Failed learned-detector gate blocks control integration

Date: September 29, 2026

Decision: Do not use the current YOLOv8n checkpoint in estimation or follower control. Keep the A012 final scenes unchanged and require a separate approved corrective detector stage before pair integration.

Reason: The checkpoint passed bearing and latency limits but reached only a 79.6% valid full-visible rate and 0.505 m range RMSE. Both results fail the approved 95% and 0.15 m limits. Advancing it would hide a known perception failure inside the controller.

## D020 Corrective detector remains blocked after independent final gate

Date: September 29, 2026

Decision: Do not lower the frozen acceptance thresholds and do not advance the corrective YOLOv8n checkpoint to pair integration. Preserve the independent `camera_calibration` and `straight_aisle` scenes as failed final-gate evidence.

Reason: The corrective dataset and validation-only calibration improved validation range RMSE, but the frozen final gate produced zero valid detections across 1,620 full-visible samples. Inference latency passed at 7.35 ms p95, but range and bearing accuracy were undefined. This is evidence of detector generalization failure, not a reason to hide or relax the gate.

## D021 Synchronized v3 closes the static learned-measurement gate

Date: September 29, 2026

Decision: Preserve the v1 and v2 failures, correct the RGB/BGR inference contract and stale-frame dataset capture, train one synchronized v3 checkpoint, and accept it as the candidate detector for a separately approved one-leader/one-follower integration stage. Do not treat the static gate as follower-control evidence.

Reason: Diagnosis found that the ROS node supplied RGB arrays to an Ultralytics array interface that expects BGR and that two settled frames could leave images at the previous target pose. The v3 dataset used eight settle frames, an offline visibility and alignment audit, separate train/validation/test scenes, validation-only threshold and range calibration, and two scenes sealed before training. Its final gate achieved 100% valid full-visible measurements, 0.0323 m range RMSE, 0.1569 degree bearing MAE, and 9.02 ms p95 inference latency. These results pass the frozen static-measurement limits but do not establish estimator, controller, motion, physical-robot, or safety performance.

## D022 Validate a nominal pair before chain expansion

Date: September 29, 2026

Decision: Use a deterministic bounded velocity route for the leader and validate exactly one independently driven follower before adding another follower or a route planner. The follower uses only its forward RGB stream and local wheel odometry. A relative range-bearing EKF, bounded controller, and `TRACK`, `PREDICT`, and `SAFE STOP` supervisor run in `/follower_1`. Gazebo poses remain inside `ee616_evaluation`.

Reason: The pair is the minimum scientific unit. Repeated straight and gradual-turn runs isolate moving-image detection, estimation, physics, supervision, and closed-loop spacing before rearward error propagation is introduced. All six nominal runs passed, but this decision does not claim disturbance, multi-follower, physical-robot, or safety validation.

## D023 Expand only through a staged incremental chain

Date: September 30, 2026

Decision: Add Follower 2 first and require its six-run nominal matrix to pass before adding Follower 3. Give every follower the same RGB, local-odometry, estimator, supervisor, and controller pipeline under an isolated namespace. Measure each predecessor-follower pair separately and retain the result even if rearward error does not increase.

Reason: The two-follower stage passed before the three-follower stage was launched. All 12 runs passed the approved limits. In the three-follower matrix, mean RMSE decreased from 0.0775 m to 0.0628 m to 0.0512 m toward the rear. Therefore, this nominal result does not demonstrate rearward error amplification. It establishes bounded nominal chain operation only and does not claim controlled-disturbance, physical-robot, or safety validation.

## D024 Freeze a pair-first controlled-disturbance matrix

Date: September 30, 2026

Decision: Test sharp turns, 0.5-second and 1.3-second full-frame RGB blackouts, a four-second stopped leader, and a 0.5-second post-controller yaw-command bias of 0.15 rad/s. Require three repetitions of all five pair scenarios to pass before running three combined three-follower trials. Keep the acceptance limits unchanged after the repeated matrix begins.

Reason: The pair remains the minimum scientific unit, and the chain should not hide a pair-level recovery failure. An initial repeated matrix exposed a startup race: one long-occlusion trial began leader motion before the detector produced a valid measurement. The chain stage correctly remained blocked. The stationary initialization window was increased from four to eight seconds, and the event schedule and evaluation window were shifted by the same four seconds without changing any acceptance threshold. The corrected 15-run pair matrix and three combined chain runs passed. Mean combined-scenario RMSE increased toward the rear. The stopped-leader follower settled to nearly zero command but retained about 0.12 m of short-gap undershoot because the controller does not reverse. The RGB blackout is not physical occlusion, and the yaw bias is not wheel slip or a motor-fault model.

## D025 Close Gate 6 with observer-only timing and bounded evaluator recovery

Date: September 30, 2026

Decision: Measure timing through an observer that subscribes to existing ROS topics without publishing into perception, estimation, supervision, or control. Reuse the accepted combined three-follower disturbance scenario for three repetitions. Keep the frozen latency, delivery, real-time-factor, RAM, and VRAM limits. Permit up to three attempts for a Gazebo pose CLI read and fail the behavior evaluator after three consecutive failed sample reads.

Reason: The first Gate 6 execution was incomplete because a transient `gz topic` segmentation fault terminated the behavior evaluator and shut down the timing observer before it wrote run 1. The available timing values were within limits, so changing the detector or controller was not justified. The evaluator-only repair retained the scientific criteria and added explicit failure evidence for interrupted observers. The repeated three-run matrix then passed every frozen aggregate check. This establishes timing and resource feasibility only for the target-laptop simulation configuration; it does not establish network, physical-actuator, physical-robot, or safety performance.

## D026 Freeze the completed simulation evidence and separate the learning handbook

Date: September 30, 2026

Decision: Close the planned seven-gate simulation sequence by freezing the accepted Gate 1--6 source, protocols, configurations, raw results, summaries, figures, failed detector attempts, and evidence limits under a SHA-256 manifest. Package a separate indexed technical handbook and evidence walkthrough for operation, study, and review. Treat the handbook as learning and project-use documentation, not as Neeraj's faculty-authored report.

Reason: The accepted gates now cover environment verification, static learned measurement, pair integration, incremental chain expansion, controlled disturbances, and target-laptop timing. A machine-verifiable archive makes those results reproducible and preserves failures as part of the technical record. Keeping the handbook separate supports Neeraj's understanding without silently replacing his own faculty-facing writing. Later experiments require a new approved scope and must not overwrite the frozen evidence.
