DOCKER ?= docker
COMPOSE := $(DOCKER) compose
DEV_COMPOSE := $(COMPOSE) -f compose.yaml -f .devcontainer/compose.yaml
SCENARIO ?= straight_aisle

.PHONY: aws-benchmark aws-warehouse-gui container-build container-config \
	container-shell environment-check environment-check-gpu gazebo-gui gpu-shell \
	prepare-display scenario-gui scenario-validate vscode yolo-dataset-capture \
	chain-gate disturbance-gate pair-gate timing-gate \
	yolo-dataset-v2 yolo-dataset-v3 yolo-diagnose-v2 yolo-gate yolo-gate-v2 \
	yolo-gate-v3 yolo-model-acquire yolo-train yolo-train-v2 yolo-train-v3

container-build:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) build

container-config:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) config --quiet

container-shell:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev

environment-check:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm check

environment-check-gpu:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu /workspace/infrastructure/docker/run_environment_check.sh

prepare-display:
	bash infrastructure/dev/prepare_xauthority.sh

gazebo-gui: prepare-display
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(DEV_COMPOSE) run --rm dev bash /workspace/infrastructure/dev/launch_playground.sh

scenario-gui: prepare-display
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(DEV_COMPOSE) run --rm dev bash /workspace/infrastructure/dev/launch_scenario.sh $(SCENARIO)

scenario-validate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev bash /workspace/infrastructure/benchmarks/validate_scenarios.sh

aws-warehouse-gui: prepare-display
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(DEV_COMPOSE) run --rm dev bash /workspace/infrastructure/dev/launch_aws_warehouse.sh

aws-benchmark:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu bash /workspace/infrastructure/benchmarks/run_aws_world_benchmark.sh

gpu-shell:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu

vscode:
	code .

pair-gate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_pair_gate.sh

chain-gate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_chain_gate.sh

disturbance-gate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_disturbance_gate.sh

timing-gate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_timing_gate.sh

yolo-model-acquire:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev \
		python3 /workspace/work/ros2_ws/scripts/acquire_yolov8n_checkpoint.py

yolo-dataset-capture:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev \
		bash /workspace/work/ros2_ws/scripts/capture_yolo_dataset.sh

yolo-dataset-v2:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev \
		bash /workspace/work/ros2_ws/scripts/capture_yolo_dataset_v2.sh

yolo-dataset-v3:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) run --rm dev \
		bash /workspace/work/ros2_ws/scripts/capture_yolo_dataset_v3.sh

yolo-diagnose-v2:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/capture_yolo_v2_failure_diagnostics.sh

yolo-train:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolov8n_training.sh

yolo-train-v2:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolov8n_v2_training.sh

yolo-train-v3:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolov8n_v3_training.sh

yolo-gate:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolo_measurement_gate.sh

yolo-gate-v2:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolo_measurement_gate_v2.sh

yolo-gate-v3:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu \
		bash /workspace/work/ros2_ws/scripts/run_yolo_measurement_gate_v3.sh
