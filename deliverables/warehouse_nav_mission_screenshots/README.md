# Mapped Warehouse Mission Screenshots

These 1920 by 1080 images are frames from
`../Neeraj_Kanchani_EE616_Hybrid_AStar_Warehouse_Demo.mp4`.

| File | Video time | Visible event |
|---|---:|---|
| `01_receiving_loading.png` | 00:25 | Sequential receiving-dock loading; all three supervisor states are visible |
| `02_bottom_aisle.png` | 01:15 | Convoy approaching the first mapped aisle turn |
| `03_hybrid_astar_turn.png` | 02:05 | Hybrid-A* route execution through the cross-aisle transition |
| `04_dispatch_unloading.png` | 03:40 | Convoy settled at the separate dispatch dock before unloading |

The dashboard is read only. Only Follower 1's RGB stream is displayed to reduce
presentation observer load, while the state labels for all three followers
remain visible. The route completed and sampled collisions were zero. The GUI
run's 0.890 real-time factor missed the headless timing limit because rendering
and recording were active, so these frames are visual aids rather than timing
evidence, additional repetitions, or physical-robot evidence.
