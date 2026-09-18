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
