FROM ros:jazzy-ros-base-noble

ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        jq \
        libgl1-mesa-dri \
        mesa-utils \
        procps \
        python3-colcon-common-extensions \
        python3-pip \
        python3-flake8 \
        python3-pytest \
        python3-rosdep \
        python3-yaml \
        ros-jazzy-camera-info-manager \
        ros-jazzy-image-transport \
        ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

COPY infrastructure/docker/requirements-vision.txt /tmp/requirements-vision.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
        -r /tmp/requirements-vision.txt

COPY infrastructure/docker/entrypoint.sh /usr/local/bin/ee616-entrypoint
COPY infrastructure/docker/healthcheck.sh /usr/local/bin/ee616-healthcheck
RUN chmod 0755 /usr/local/bin/ee616-entrypoint /usr/local/bin/ee616-healthcheck

ENV ROS_DISTRO=jazzy \
    ROS_DOMAIN_ID=57 \
    RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    GZ_PARTITION=ee616

WORKDIR /workspace/work/ros2_ws

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD ["/usr/local/bin/ee616-healthcheck"]

ENTRYPOINT ["/usr/local/bin/ee616-entrypoint"]
CMD ["bash"]
