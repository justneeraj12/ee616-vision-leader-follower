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

## Next approval required

The ROS 2 Jazzy and Gazebo Harmonic environment-validation gate has not yet been approved for implementation. Its approval packet should define installation boundaries, smoke tests, expected resource measurements, files changed, rollback steps, and the evidence required before the camera-measurement experiment begins.
