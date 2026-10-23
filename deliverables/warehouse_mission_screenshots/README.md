# Warehouse Mission Screenshots

These are full-resolution frames from the recorded ROS 2 and Gazebo warehouse
mission. They are presentation artifacts, not independent experiment runs.

| File | Source | Visible state |
|---|---|---|
| `01_loading_queue.png` | Live capture during the recording | Robots entering the loading point in order; all three followers in `TRACK` |
| `02_loaded_convoy.png` | Live capture during the recording | Four blue cargo boxes and convoy travel in `WAREHOUSE_AISLE` |
| `03_dropoff_approach.png` | Video frame at 76 s | Convoy stopped in `DROPOFF_SETTLE` |
| `04_unloading.png` | Video frame at 84 s | Completed mission after sequential unloading |

The left window is Gazebo. The right window is a read-only dashboard of all
three follower cameras and supervisor states. The blue cargo boxes are moved by
scripted presentation joints. They do not demonstrate grasping or autonomous
manipulation.
