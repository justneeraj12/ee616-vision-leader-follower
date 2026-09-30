# Approval Log

This log records implementation scopes approved by Neeraj Kumar Kanchani. A new implementation stage should not begin until its objective, acceptance criteria, evidence, and documentation changes are recorded here.

## A001 Initial toy simulation baseline

Status: Approved and completed

Approved scope: Build initial deterministic toy simulations and produce preliminary evidence suitable for faculty review.

Delivered evidence: Repeatable metrics, figures, source package, report, and two-dimensional demonstration video.

## A002 Multi-follower warehouse maze

Status: Approved and completed

Approved scope: Add more followers and demonstrate them in a warehouse-style maze.

Delivered evidence: One leader, three followers, six shelf blocks, seven route segments, recorded metrics, source package, and demonstration video.

## A003 Industry application report

Status: Approved and completed

Approved scope: Explain the industrial application, leader and follower roles, usefulness, production-level architecture, limitations, and safety boundary in Neeraj's formal first-person voice.

Delivered evidence: Editable DOCX and review-ready PDF in `deliverables/`.

## A004 Project workspace consolidation

Status: Approved and completed

Approved scope: Consolidate the project under `/home/justneeraj/Documents/MS_sem3/GRAD_PROJECT` without deleting the previous copies.

Delivered evidence: Organized deliverables, work, references, project index, repaired internal paths, and passing toy-simulation tests.

## A005 Master prompt and operating documentation

Status: Approved and completed

Approved scope: Create a reusable project prompt that captures the technical requirements, writing voice, approval workflow, evidence standards, folder rules, and proactive planning expectations.

Delivered evidence: `PROJECT_MASTER_PROMPT.md`, current project status, decision log, approval log, and project-index links.

## A006 Initial technical explanation and private GitHub repository

Status: Approved and completed

Approved scope: Create a polished faculty-review report with technical explanation and preliminary figures, update the governing documentation, create a private GitHub repository, and push the curated project files.

Acceptance criteria: Use Neeraj's formal first-person voice; trace numerical claims to recorded evidence; keep ground truth outside the control path; distinguish toy evidence from ROS 2, Gazebo, physical-robot, and production-safety evidence; deliver matching DOCX and PDF files; visually inspect every rendered page; exclude temporary and quality-check artifacts from GitHub; and use no force push.

Delivered evidence: Eight-page DOCX and PDF report, four source figures, report builder, passing toy-simulation tests, document quality checks, updated project records, and the private repository `https://github.com/justneeraj12/ee616-vision-leader-follower`.

## A007 Production-style repository documentation and CI

Status: Approved and completed

Approved scope: Rework the repository landing page to match the quality and structure of Neeraj's recent repositories, add continuous integration for the existing toy baseline, make dependencies and reproduction commands explicit, add contribution and citation files, update the governing documentation, and push the verified changes to the private GitHub repository.

Acceptance criteria: Keep measured and planned work separate; retain the toy, Gazebo, physical-robot, and production-safety evidence boundaries; provide working clean-checkout commands; run all seven tests locally; test Python 3.11 and 3.12 in GitHub Actions; validate README links and repository metadata; exclude credentials and temporary artifacts; and use no force push.

Delivered evidence: Production-style README, architecture and validation roadmap, video and faculty-deliverable links, GitHub Actions workflow, contribution guide, changelog, citation metadata, explicit package extras, updated project records, local clean-install verification, and a reviewable Git commit.

## A008 Single-column IEEE LaTeX technical report

Status: Approved and completed

Approved scope: Create a separate version of the initial technical explanation using the IEEEtran LaTeX class in single-column mode. Preserve the existing submitted report and reuse only the four verified figures and recorded toy-simulation evidence.

Acceptance criteria: Use simple formal English in Neeraj's first-person voice; keep the application, research question, current evidence, limitations, next technical gate, and faculty questions; distinguish toy evidence from ROS 2, Gazebo, physical-robot, and production-safety evidence; compile without unresolved citations, references, or margin overflow; and visually inspect every page.

Delivered evidence: Editable LaTeX and BibTeX source under `work/ieee_simple_report/` and a five-page, single-column IEEE-style PDF under `deliverables/`. The PDF contains four verified figures, four external references, traceable project evidence paths, complete metadata, and no unsupported safety or production claim.

## A009 Containerized ROS 2 and Gazebo foundation

Status: Approved and completed

Approved scope: Organize the ROS 2 workspace, create a canonical Docker environment for ROS 2 Jazzy and Gazebo Harmonic, add namespace and camera smoke tests, document leader and follower sensor boundaries, configure an optional NVIDIA GPU profile, verify the environment, update the private GitHub repository, and preserve all unrelated uncommitted work.

Acceptance criteria: Build from an official ROS Jazzy Ubuntu Noble image; provide ROS 2, Gazebo Harmonic, and `ros_gz`; build the workspace with `colcon`; pass two-namespace isolation checks; launch a minimal headless Gazebo camera world; bridge timestamped camera images to ROS 2; document CPU and GPU paths; record machine-readable evidence; keep ground truth outside the control path; and do not claim follower-performance evidence from an environment smoke test.

Delivered evidence: Canonical ROS 2 Jazzy and Gazebo Sim 8.15.0 container; two ROS packages built; two package tests passed; isolated `/leader` and `/follower_1` namespace probes passed; 15 timestamped 640×480 RGB camera samples bridged from Gazebo; machine-readable evidence saved under `work/ros2_ws/results/environment_gate/`; and NVIDIA container access verified for the RTX 3050 Ti with 4096 MiB VRAM. GPU rendering acceleration remains unbenchmarked.

## A010 Integrated VS Code and Gazebo learning workspace

Status: Approved and completed

Approved scope: Add a VS Code Dev Container based on the canonical ROS image, integrated terminals and tasks for building, testing, launching, inspecting, and stopping the simulation, a safely forwarded Gazebo GUI, an editable warehouse playground, and learning documentation with architecture maps and metric explanations. Preserve the report and unrelated reference files.

Acceptance criteria: Use the existing authorized workspace and Docker image; avoid unrestricted display permissions; keep generated files owned by the development user; open the Gazebo GUI; expose ROS nodes and topics to an integrated learning shell; retain the headless environment gate; pass ROS and toy tests; document every command and evidence limitation; and leave report files untouched.

Delivered evidence: The Dev Container ran as the non-root `ubuntu` user; two ROS packages built; three ROS package tests and seven toy tests passed; the six-shelf playground opened in Gazebo Sim 8.15.0; 15 timestamped 640×480 RGB samples crossed the Gazebo-to-ROS bridge; the ROS learning shell and stop task were exercised; X11 access used a copied temporary authorization file; and workflow, learning-map, metric, and evidence-limit documentation was added. Mesa/GLX/EGL fallback warnings were observed, so GPU-accelerated rendering remains unverified.

## A011 Deterministic scenario templates and AWS compatibility benchmark

Status: Approved and completed

Approved scope: Add changeable deterministic Gazebo scenario templates, preserve controlled scenes as the primary measurement environments, import a pinned no-roof subset of the AWS small warehouse for optional Harmonic compatibility testing, measure laptop resource use, update the integrated workflow and documentation, and preserve unrelated report and reference files.

Acceptance criteria: Generate reproducible SDF and manifests from bounded YAML; validate camera transport in each controlled scene; keep imported-source provenance and license; leave the vendor source world unchanged; run the AWS scene headlessly and graphically; record camera delivery, real-time factor, CPU, memory, and visible GPU measurements; keep ground truth outside the control path; and make no detector, control, collision-safety, or production claim.

Delivered evidence: Five deterministic scenarios each delivered 30 timestamped 640×480 RGB frames; six ROS package tests and seven toy tests passed; the AWS no-roof scene delivered 150 of 150 camera frames at 15.19 Hz; median real-time factor was 0.9999; peak container memory was 364.7 MiB; CPU use was 47.9% of one core equivalent; visible NVIDIA memory was 253 MiB; peak reported GPU utilization was 19%; no fatal asset or plugin errors were detected; and the graphical world opened in Gazebo Sim 8.15.0. Mesa/GLX/EGL warnings mean GPU rendering acceleration remains unverified.

## A012 Camera-only range and bearing baseline

Status: Approved and completed

Approved scope: Add a camera-only fixed-red-target detector, compute range and positive-left bearing from image geometry, add a separate evaluation-only Gazebo ground-truth package, run open-scene and structured-aisle sweeps, retain failed and occluded conditions, create raw and summarized evidence, and preserve unrelated report and reference files.

Acceptance criteria: Use 1.0, 1.5, 2.0, 3.0, 4.0, and 5.0 m ranges; use -30, -20, -10, 0, 10, 20, and 30 degree bearings; record at least 30 frames per condition at 640×480 and 15 Hz; achieve at least 95% valid full-visible measurements, range RMSE no more than 0.15 m, and bearing MAE no more than 1.5 degrees; keep Gazebo ground truth out of perception, estimation, supervision, and control; and retain limitations and excluded visibility cases.

Delivered evidence: Two new ROS 2 packages; 19 passing ROS package tests across the workspace; 2,520 retained Gazebo samples across two scenes; 1,620 full-visible samples; 100% valid full-visible measurements; 0.0355 m combined range RMSE; 0.120 degree combined bearing MAE; raw CSV files, scene and combined JSON summaries, and an error figure under `work/ros2_ws/results/camera_measurement_gate/`. The result is a fixed-red-target camera-geometry baseline, not YOLO, closed-loop control, physical-robot, or safety evidence.

## A013 YOLOv8n measurement evaluation

Status: Approved and evaluated; acceptance criteria not met

Approved scope: Add an isolated YOLOv8n detector backend, train or fine-tune it on a documented custom target dataset, and evaluate it against the frozen A012 range and bearing matrix before it enters any follower-control path.

Acceptance criteria: At least 95% valid full-visible measurements; range RMSE no more than 0.15 m; bearing MAE no more than 1.5 degrees; p95 detector latency no more than 66.7 ms for a 15 Hz target; record false detections, CPU, RAM, GPU, and VRAM use; record model provenance, version, license, and checksum; and keep Gazebo ground truth restricted to evaluation.

Delivered evidence: The 648-image dataset, isolated RGB-only backend, trained checkpoint, checksums, training logs, held-out test, frozen A012 measurement rows, timing, and resource logs are complete. The held-out dataset test recorded 123 true positives, 28 true negatives, nine false negatives, and two false positives. The final gate recorded 2,520 samples and 1,620 full-visible samples. Bearing MAE was 0.153 degrees and p95 inference latency was 9.13 ms, so those limits passed. The valid full-visible rate was 79.6% and range RMSE was 0.505 m, so the overall gate failed. The checkpoint must not enter follower control.

## A014 Public AGPL repository

Status: Approved and completed

Approved scope: Release the existing GitHub repository and its full history as public, license original project software and documentation under AGPL-3.0-only, preserve third-party terms, document the decision, commit and push the publication changes, and change repository visibility to public.

Acceptance criteria: Scan the current tree and Git history for high-confidence credential patterns; disclose the personal, faculty, internal-log, deliverable, and third-party-reference exposure before publication; add the canonical GNU AGPL-3.0 text; replace proprietary ROS manifest declarations; preserve the AWS MIT license; add third-party notices; pass the existing automated tests; use no history rewrite or force push; and leave unrelated untracked files untouched.

Delivered evidence: No high-confidence credential pattern was found in the current tree or Git history. The repository contains an AGPL-3.0-only license, updated ROS package declarations and citation metadata, and explicit third-party notices. The complete existing history was retained without rewriting. Seven toy tests and 19 ROS package tests passed before publication.

## A015 Ubuntu 26.04 host compatibility and revalidation

Status: Approved and completed

Approved scope: Correct the Docker APT source after the laptop upgrade to Ubuntu 26.04.1 LTS, retain the canonical ROS 2 Jazzy and Gazebo Harmonic container, remove stale host-shell ROS startup lines, rebuild the approved vision dependencies, rerun the full environment and GPU checks, and update the governing documentation. Preserve unrelated report and reference files.

Acceptance criteria: Use Docker packages for Ubuntu Resolute; do not treat the host's partial ROS 2 Lyrical installation as project evidence; keep the Ubuntu Noble/Jazzy/Harmonic container reproducible; build all four ROS packages; pass all ROS and toy tests; pass namespace and Gazebo camera smoke tests; verify CUDA access on the RTX 3050 Ti; record exact dependency versions and evidence limits; and do not commit or push without separate approval.

Delivered evidence: Docker Engine 29.8.1 runs from the Resolute source; the previous source file is retained under `/var/backups/`; four ROS packages built; 19 ROS tests and seven toy tests passed; `/leader` and `/follower_1` namespace probes passed; Gazebo delivered 15 timestamped 640×480 RGB frames; and PyTorch 2.9.1 completed a CUDA tensor operation on the RTX 3050 Ti. The container also records torchvision 0.24.1 and Ultralytics 8.4.165. These checks establish environment compatibility only, not YOLO detector performance or follower-control performance.

## A016 YOLOv8n corrective detector evaluation

Status: Approved and evaluated; acceptance criteria not met

Approved scope: Add detector box and confidence diagnostics, create a separate higher-variation dataset with explicit 1.0 m coverage, train one corrective YOLOv8n checkpoint on the target laptop, derive any linear range calibration from validation data only, and rerun the unchanged A012 final measurement scenes. Do not begin pair integration unless the learned detector passes.

Acceptance criteria: Preserve complete scene separation; use no `camera_calibration` or `straight_aisle` image for training, validation, or dataset testing; retain at least 95% valid full-visible measurements; range RMSE no more than 0.15 m; bearing MAE no more than 1.5 degrees; p95 latency no more than 66.7 ms; record resource use and checksums; keep Gazebo truth evaluation-only; and preserve unrelated uncommitted files.

Delivered evidence: The validated dataset contains 1,125 images: 675 training, 225 validation, and 225 held-out test images, with zero identical images across splits and aggregate SHA-256 `e42368ae861b468206a9f7bec435508a214bc46e333f8c891b87f2cd50a00e15`. Training stopped at epoch 40 and retained best epoch 28 with checkpoint SHA-256 `cd949c617eaff472417425db025b03fc5b6c9b7698d884cdc7c8562ee930bf62`. The held-out dataset test recorded 166 true positives, 23 true negatives, 25 false negatives, and 11 false positives. Validation-only calibration used 97 samples and reduced validation range RMSE from 0.083 m to 0.051 m. The frozen final gate retained 2,520 samples and 1,620 full-visible samples but produced zero valid detections. Latency passed at 7.35 ms p95; range and bearing errors were undefined. The checkpoint remains blocked from control. Twenty-nine ROS package tests pass.

## A017 Synchronized YOLOv8n v3 diagnosis and sealed evaluation

Status: Approved and completed; acceptance criteria met

Approved scope: Diagnose the failed final-scene detector domain, correct confirmed image-contract or dataset-synchronization faults, create a separate domain-varied v3 dataset, select confidence and any range calibration from validation data only, and evaluate one new checkpoint on new scenes sealed before training. Do not begin pair integration unless the learned measurement gate passes.

Acceptance criteria: Preserve prior failed evidence; keep all sealed final images out of training, validation, held-out dataset testing, threshold selection, and calibration; verify image-label synchronization; retain at least 95% valid full-visible measurements; range RMSE no more than 0.15 m; bearing MAE no more than 1.5 degrees; p95 latency no more than 66.7 ms; record checksums and laptop resources; keep Gazebo truth evaluation-only; and preserve unrelated uncommitted files.

Delivered evidence: Diagnosis found an RGB/BGR inference mismatch and stale-frame labels. The v3 dataset contains 1,001 images with zero cross-split duplicate images and SHA-256 `574c362dd6877cfc63079b959029ae4e2e0c184b294154f759b498a7fb158a33`. The visibility filter removed 39 fully occluded or unrendered projections, and the alignment audit passed all images. Training completed 50 epochs, retained best epoch 49, and produced checkpoint SHA-256 `3ceabbabd0bccf721fcd9954b4eaffebef7b05f2572e43393a1df7568707391a`. Validation selected confidence 0.40 and calibration reduced validation range RMSE from 0.0783 m to 0.0251 m on 58 samples. The sealed gate retained 2,520 samples and passed with 1,620 of 1,620 valid full-visible measurements, 0.0323 m range RMSE, 0.1569 degree bearing MAE, and 9.02 ms p95 latency. Thirty ROS package tests pass. This is static learned-measurement evidence only.

## A018 Nominal one-leader/one-follower integration

Status: Approved and completed; acceptance criteria met

Approved scope: Integrate one deterministic leader and one independently driven follower using the v3 RGB measurement, local wheel odometry, a relative-state EKF, bounded formation control, and `TRACK`, `PREDICT`, and `SAFE STOP` supervision. Run repeated nominal straight and gradual-turn experiments. Keep Gazebo pose truth evaluation-only. Do not add followers, route planning, assignments, or disturbance experiments in this stage.

Acceptance criteria: Use isolated `/leader` and `/follower_1` namespaces; restrict follower inputs to RGB measurements and local odometry; keep Gazebo truth out of perception and control; test all three supervisor states; complete three straight and three gradual-turn runs; retain spacing RMSE no more than 0.20 m; record zero collision samples under the defined evaluator; keep p95 control period no more than 66.7 ms; bound commands to 0.0--0.6 m/s and plus or minus 0.8 rad/s; record synchronized raw evidence and laptop resources; and preserve prior work.

Delivered evidence: Five ROS 2 packages build and 39 package tests pass. All six nominal runs passed. Worst straight spacing RMSE was 0.0558 m and worst gradual-turn spacing RMSE was 0.1005 m. The minimum TRACK fraction was 99.1%, p95 control period was 50.0 ms, and the evaluator recorded zero collision samples. The six-run resource window used 1,330.8 MiB peak container memory, 383 MiB peak visible GPU memory, 27% peak GPU utilization, and 152.1% of one CPU-core equivalent. Gazebo pose data was read only by `ee616_evaluation`. This is nominal one-pair simulation evidence, not disturbance, multi-follower, physical-robot, or safety evidence.

## A019 Nominal incremental-chain integration

Status: Approved and completed; acceptance criteria met

Approved scope: Add Follower 2 and then Follower 3 only after the preceding stage passes. Reuse the validated RGB measurement, local wheel odometry, EKF, bounded controller, and supervisor under isolated namespaces. Run repeated nominal straight and gradual-turn profiles, measure every adjacent predecessor-follower pair, retain resource evidence, and preserve the evaluation-only ground-truth boundary.

Acceptance criteria: Complete three straight and three gradual-turn runs at each chain length; require the two-follower stage to pass before launching three followers; retain Follower 1 spacing RMSE no more than 0.20 m and later-follower RMSE no more than 0.25 m; keep TRACK fraction at least 95%; record zero evaluator collision samples; keep p95 control period no more than 66.7 ms; keep commands bounded to 0.0--0.6 m/s and plus or minus 0.8 rad/s; record rearward error whether favorable or unfavorable; and keep visible GPU memory within 4,096 MiB.

Delivered evidence: Five ROS 2 packages build and 44 package tests pass. The six two-follower runs passed before the six three-follower runs were launched, and all 12 runs passed. In the three-follower matrix, worst RMSE was 0.1004 m, 0.0739 m, and 0.0523 m from Follower 1 through Follower 3. The minimum TRACK fraction was 95.0%, the worst p95 control period was 50.0 ms, and the evaluator recorded zero collision samples. Mean RMSE decreased toward the rear, so rearward amplification was not observed. The resource window used 3,376.6 MiB peak container memory and 736 MiB peak visible GPU memory. Gazebo pose truth remained inside `ee616_evaluation`. This is nominal incremental-chain simulation evidence, not controlled-disturbance, physical-robot, person-safety, or production evidence.

## A020 Pair-first controlled-disturbance evaluation

Status: Approved and completed; acceptance criteria met

Approved scope: Test sharp turns, short and long visual loss, stopped-leader behavior, and a bounded actuator disturbance on the validated pair. Run a combined three-follower scenario only after every pair trial passes. Retain synchronized raw evidence, resource measurements, checksums, and the evaluation-only ground-truth boundary.

Acceptance criteria: Complete three repetitions of five pair scenarios before three combined chain runs; retain Follower 1 spacing RMSE no more than 0.30 m and later-follower RMSE no more than 0.35 m; keep TRACK fraction at least 85%; record zero evaluator collision samples; keep p95 control period no more than 66.7 ms; keep commands bounded to 0.0--0.6 m/s and plus or minus 0.8 rad/s; verify required `PREDICT`, `SAFE STOP`, zero-command, and reacquisition behavior; keep visible GPU memory within 4,096 MiB; and preserve unfavorable results and prior work.

Delivered evidence: Five ROS 2 packages build and 54 package tests pass. The 15 pair runs passed before the three combined three-follower runs were launched, and all 18 runs passed. Pair worst spacing RMSE ranged from 0.0536 m for actuator bias to 0.1247 m for the sharp turn. In the combined matrix, worst RMSE was 0.1007 m, 0.1242 m, and 0.1403 m from Follower 1 through Follower 3, so this matrix showed rearward error growth. All runs recorded zero collision samples, worst p95 control period was 50.0 ms, and combined-run p95 inference latency was at most 17.1 ms. The 620.0-second resource window used 3,511.9 MiB peak container memory and 642 MiB peak visible GPU memory. The first repeated attempt exposed and retained a detector-startup diagnosis; the corrected protocol used an eight-second stationary initialization window without changing acceptance limits. Stopped-leader commands settled near zero with about 0.12 m short-gap undershoot. Gazebo truth remained inside `ee616_evaluation`. Camera loss was a synthetic RGB blackout and the actuator disturbance was a bounded yaw-command bias, not physical occlusion, wheel slip, physical-robot, person-safety, or production evidence.

## A021 Target-laptop timing and resource gate

Status: Approved and completed; acceptance criteria met

Approved scope: Add evaluation-only timing observation to the accepted combined three-follower Gate 5 scenario, run three repetitions on the target laptop, record container and NVIDIA resource time series, verify that accepted behavior remains unchanged, and repair evaluator lifecycle faults without changing the detector, controller, route, disturbances, or frozen thresholds.

Acceptance criteria: Complete three timing and three corresponding behavior summaries; keep p95 camera-to-measurement and measurement-to-controller latency no more than 66.7 ms; keep p95 controller-to-post-proxy latency no more than 50.0 ms; keep p95 detector inference and control period no more than 66.7 ms; retain at least 95% measurement delivery; retain simulation real-time factor of at least 0.90; keep peak visible GPU memory within 4,096 MiB and peak container memory within 12,288 MiB; require accepted Gate 5 behavior checks to pass; keep Gazebo truth evaluation-only; and preserve unrelated work.

Delivered evidence: Five ROS 2 packages build and 59 package tests pass. The first full execution was incomplete after a transient `gz topic` segmentation fault shut down run 1; the evaluator-only repair added bounded pose-read recovery and explicit interrupted-observer evidence without changing scientific thresholds. The repeated matrix completed three timing and three behavior runs, and every aggregate check passed. Worst p95 camera-to-measurement latency was 23.09 ms, measurement-to-controller latency was 48.35 ms, controller-to-post-proxy latency was 2.89 ms, detector inference was 20.34 ms, and control period was 50.0 ms. Minimum delivery ratio was 95.4%, and minimum real-time factor was 0.9996. The 158.9-second resource window used 3,584.0 MiB peak container memory, 642 MiB peak visible GPU memory, 60% peak GPU utilization, and 443.1% of one CPU-core equivalent. This is one-host simulation evidence, not network, physical-actuator, physical-robot, person-safety, or production evidence.

## A022 Gate 7 evidence freeze, handbook, video, and review package

Status: Approved and completed; acceptance criteria met

Approved scope: Freeze the accepted Gate 1--6 experiments and their failed detector history; create a final evidence index, an indexed LaTeX technical handbook and simulation user guide, a concise evidence walkthrough video, and a checksum-verifiable repository review archive. Update the governing logs without committing or pushing.

Acceptance criteria: Preserve accepted and failed evidence; include machine-readable expected statuses and SHA-256 checksums; compile and visually verify the indexed handbook; explain setup, daily use, Gazebo interaction, configurations, algorithms, metrics, results, limitations, troubleshooting, and oral-defense preparation; create and inspect a 1920 by 1080 evidence video; pass at least 59 ROS package tests and all seven toy tests; make no physical-robot, person-safety, certification, or production-readiness claim; and preserve unrelated uncommitted changes.

Delivered evidence: The frozen manifest records all expected Gate 1--6 statuses, including the retained v1 and v2 detector failures. Five ROS packages built and 59 tests passed with zero failures; seven toy tests passed. The 68-page handbook compiled with a generated index and was visually checked after rendering every page. The silent evidence walkthrough is 1920 by 1080, 30 frames per second, and 40 seconds long. The final evidence index, verification script, checksum file, package builder, and review ZIP preserve the frozen file set. The package is simulation evidence only. No commit or push was performed.

## Next approval required

The planned seven-gate simulation sequence is complete. Any faculty-requested change, physical-robot stage, new experiment matrix, report-authoring stage, commit, or push requires separate explicit approval.
