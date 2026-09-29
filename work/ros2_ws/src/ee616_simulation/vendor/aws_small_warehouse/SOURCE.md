# AWS RoboMaker Small Warehouse Assets

This directory contains a selected, pinned subset of the archived AWS RoboMaker
Small Warehouse World assets.

- Upstream repository: `aws-robotics/aws-robomaker-small-warehouse-world`
- Harmonic conversion source: `Juancams/aws-robomaker-small-warehouse-world`
- Source commit: `a8ba1cea777799d51db58f759e4d2cfa2c81fd74`
- Upstream pull request: `aws-robotics/aws-robomaker-small-warehouse-world#27`
- Download archive SHA-256:
  `e1500b30de29948e4c222d72d4ce5e0f589c55133a0f2070ca5ada654e5f3b19`
- License: the included `LICENSE` file

Only the models referenced by the no-roof warehouse and the no-roof source
world are retained. Obsolete launch files, maps, screenshots, the roof model,
the unused desk model, and operating-system metadata are not included.

The source world remains unchanged in this vendor directory. The EE 616 launch
path creates a runtime copy that adds a fixed camera and visual target for
transport and resource benchmarking. This imported world is an optional visual
stress test. It is not the primary scientific validation environment.
