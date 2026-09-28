#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script with sudo." >&2
    exit 1
fi

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg

install -m 0755 -d /usr/share/keyrings
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    > /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit

if [[ -f /etc/docker/daemon.json ]]; then
    cp --preserve=all /etc/docker/daemon.json /etc/docker/daemon.json.ee616-backup
fi

nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

echo "NVIDIA Container Toolkit is installed and Docker has been restarted."
echo "Verify with: sudo docker run --rm --gpus all ubuntu nvidia-smi"
