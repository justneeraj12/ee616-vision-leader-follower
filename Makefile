DOCKER ?= docker
COMPOSE := $(DOCKER) compose

.PHONY: container-build container-config container-shell environment-check \
	environment-check-gpu gpu-shell

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

gpu-shell:
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) $(COMPOSE) --profile gpu run --rm gpu
