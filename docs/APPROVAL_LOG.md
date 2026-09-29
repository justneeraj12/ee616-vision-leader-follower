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

Status: Approved, not yet implemented

Approved scope: Add an isolated YOLOv8n detector backend, train or fine-tune it on a documented custom target dataset, and evaluate it against the frozen A012 range and bearing matrix before it enters any follower-control path.

Acceptance criteria: At least 95% valid full-visible measurements; range RMSE no more than 0.15 m; bearing MAE no more than 1.5 degrees; p95 detector latency no more than 66.7 ms for a 15 Hz target; record false detections, CPU, RAM, GPU, and VRAM use; record model provenance, version, license, and checksum; and keep Gazebo ground truth restricted to evaluation.

Current condition: Implementation was paused for the repository and Ultralytics license review. A014 resolves the planned repository license condition, but the dependency, model, dataset, and measured detector performance remain unverified.

## A014 Public AGPL repository

Status: Approved and completed

Approved scope: Release the existing GitHub repository and its full history as public, license original project software and documentation under AGPL-3.0-only, preserve third-party terms, document the decision, commit and push the publication changes, and change repository visibility to public.

Acceptance criteria: Scan the current tree and Git history for high-confidence credential patterns; disclose the personal, faculty, internal-log, deliverable, and third-party-reference exposure before publication; add the canonical GNU AGPL-3.0 text; replace proprietary ROS manifest declarations; preserve the AWS MIT license; add third-party notices; pass the existing automated tests; use no history rewrite or force push; and leave unrelated untracked files untouched.

Delivered evidence: No high-confidence credential pattern was found in the current tree or Git history. The repository contains an AGPL-3.0-only license, updated ROS package declarations and citation metadata, and explicit third-party notices. The complete existing history was retained without rewriting. Seven toy tests and 19 ROS package tests passed before publication.

## Next approval required

A013 is approved. Before training or measurement begins, record the exact Ultralytics package and model versions, dataset provenance and split, target appearance, dependency lock, model checksum, and executable test commands.
