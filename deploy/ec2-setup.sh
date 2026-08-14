#!/usr/bin/env bash
# ==============================================================================
# One-time EC2 bootstrap script: installs Docker Engine + Compose plugin.
#
# Usage (on a fresh Ubuntu 22.04/24.04 EC2 instance):
#   sudo apt-get update && sudo apt-get install -y git
#   git clone <your-repo-url> && cd <repo>
#   bash deploy/ec2-setup.sh
#
# NOTE: "docker" group is applied at NEXT login, so log out/in once
# afterwards (or just wait — the CI/CD deploy job opens a fresh SSH
# session each run, so it will pick up the group automatically).
# ==============================================================================

set -euo pipefail

echo "==> Installing prerequisites..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git

echo "==> Adding Docker's official GPG key and repository..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

echo "==> Installing Docker Engine + Compose plugin..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Adding current user to the docker group (no sudo needed)..."
sudo usermod -aG docker "$USER"

echo "==> Verifying Docker..."
sudo docker version --format '{{.Server.Version}}'
docker compose version

echo
echo "Done. Log out and back in (or reconnect) to use docker without sudo."
echo "Then add the GitHub secrets listed in docs/deploy.md and push to main."