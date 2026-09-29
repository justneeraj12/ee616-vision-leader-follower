DOCKER ?= docker
COMPOSE := $(DOCKER) compose
DEV_COMPOSE := $(COMPOSE) -f compose.yaml -f .devcontainer/compose.yaml
SCENARIO ?= straight_aisle

.PHONY: aws-benchmark aws-warehouse-gui container-build container-config \
	container-shell environment-check environment-check-gpu gazebo-gui gpu-shell \
	prepare-display scenario-gui scenario-validate vscode

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
