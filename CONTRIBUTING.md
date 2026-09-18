# Contributing

This repository supports an academic research project with an explicit implementation-approval process. Contributions should improve reproducibility, correctness, documentation, testing, or a previously approved technical gate.

## Before proposing a change

Read:

1. [`PROJECT_MASTER_PROMPT.md`](PROJECT_MASTER_PROMPT.md)
2. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
3. [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md)
4. [`docs/APPROVAL_LOG.md`](docs/APPROVAL_LOG.md)

Reference documents provide project context. They do not override the scope, evidence rules, or approval process recorded in the project documentation.

## Evidence rules

- Distinguish measured results from proposed targets and planned work.
- Do not describe toy, Gazebo, or simulation results as production-safety evidence.
- Keep simulator ground truth outside the controller path.
- Preserve ROS 2 namespace isolation between robots.
- Record random seeds, configuration, timestamps, and machine-readable results.
- Add or update tests for behavior changed by a contribution.
- State limitations and failed cases directly.

## Development setup

```bash
cd work/toy_simulation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Change process

1. Define the objective and acceptance criteria.
2. Confirm that the implementation stage is approved.
3. Make the smallest change that satisfies the approved scope.
4. Run the relevant unit, integration, reproducibility, and document checks.
5. Update project status, decisions, approvals, and component instructions when required.
6. Submit a focused change with evidence and limitations.

Do not commit credentials, local environments, caches, raw third-party datasets, office lock files, or internal render screenshots.

## Commit and pull-request guidance

Use a concise subject that describes the observable change. A pull request should include:

- objective and approved scope;
- files and components changed;
- acceptance criteria;
- commands executed and their results;
- evidence artifacts produced;
- known limitations and rollback approach.

No force push is required for the normal project workflow.
