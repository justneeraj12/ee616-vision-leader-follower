# EE 616 Grad Project Workspace

This is the main workspace for Neeraj Kumar Kanchani's EE 616-57 grad project on vision-only leader-follower warehouse coordination.

Start new project work with [`PROJECT_MASTER_PROMPT.md`](PROJECT_MASTER_PROMPT.md). It contains the standing technical scope, writing voice, approval workflow, evidence rules, and session checklist.

For a shorter copy-and-paste entry point, use [`QUICK_START_PROMPT.md`](QUICK_START_PROMPT.md).

## Project application

The proposed application is a flexible autonomous material-delivery convoy for warehouse and manufacturing aisles. A route-owning leader executes the delivery mission. Independently driven follower carts use a forward RGB camera and local odometry to maintain formation with the robot immediately ahead.

The current implementation is a deterministic two-dimensional toy simulator. It is not yet a ROS 2 or Gazebo result and is not evidence of production safety.

## Folder structure

- `deliverables/` contains the reports, PDFs, videos, and packaged baselines intended for review or sharing.
- `work/toy_simulation/` contains the simulator source, tests, recorded data, plots, video builders, and quality-check artifacts.
- `work/professor_package/` contains the original faculty package builder and its document-render checks.
- `work/industry_application_report/` contains the industry-application report builder, architecture figure, and render checks.
- `work/technical_explanation_report/` contains the faculty technical-review report builder, four source figures, and internal render checks.
- `references/` contains the original project-scope documents supplied for the project.
- `docs/PROJECT_STATUS.md` records the verified current state, limitations, blockers, and next proposed gate.
- `docs/DECISION_LOG.md` records scope and architecture decisions.
- `docs/APPROVAL_LOG.md` records the implementation stages approved by Neeraj.

## Current review files

- `deliverables/Neeraj_Kanchani_EE616_Initial_Technical_Explanation_and_Preliminary_Figures.pdf`
- `deliverables/Neeraj_Kanchani_EE616_Initial_Technical_Explanation_and_Preliminary_Figures.docx`
- `deliverables/Neeraj_Kanchani_EE616_Industry_Application_and_System_Rationale.pdf`
- `deliverables/Neeraj_Kanchani_EE616_Industry_Application_and_System_Rationale.docx`
- `deliverables/Neeraj_Kanchani_EE616_Initial_Toy_Simulation_Results.pdf`
- `deliverables/Neeraj_Kanchani_EE616_Multi_Follower_Warehouse_2D.mp4`

## Current toy evidence

The warehouse toy run includes one leader and three followers in a six-shelf maze. The 86-second seeded run completed seven path segments with zero recorded collision samples. Spacing RMSE was 0.140 m, 0.164 m, and 0.200 m from the first to the third follower. These values describe only the idealized kinematic model.

## Approval workflow

Neeraj approves every new implementation stage before it begins. Each approval should identify the scope, expected files, acceptance criteria, tests, and documentation updates. The next proposed implementation gate is environment and reproducibility validation for ROS 2 Jazzy and Gazebo Harmonic. The measurement-only camera baseline follows only after that gate passes.

## GitHub repository

The private project repository is `https://github.com/justneeraj12/ee616-vision-leader-follower`. It contains the project documentation, source, tests, machine-readable toy evidence, report builders, and review deliverables. Internal page renders, temporary files, and quality-check screenshots are excluded.

## Reproducing the toy baseline

From `work/toy_simulation/`:

```bash
PYTHONPATH=src python3 -m toy_swarm.run --output results
PYTHONPATH=src python3 run_warehouse.py
python3 -m unittest discover -s tests -v
```

The scripts that create reports and videos resolve this project folder automatically and write reviewable files to `deliverables/`.
