# CI/CD Deployment: GitHub Actions + Docker Hub + AWS EC2

This guide walks you through deploying SmartFarm to an EC2 instance with a fully automated pipeline:

```
push to main
   │
   ▼
GitHub Actions ── CI ──► run pytest for all 4 services (.github/workflows/ci.yml)
   │
   ▼
GitHub Actions ── CD ──► build images ──► push to Docker Hub
   │                          (smartfarm-<service>:latest + :<commit-sha>)
   ▼
SSH to EC2 ──► docker compose pull ──► docker compose up -d ──► app on :3000
```

The EC2 server **never builds images**. It only pulls ready-made images from
Docker Hub using `docker-compose.prod.yaml` (no `build:` sections, no source code needed).

---

## 1. Prerequisites

| Item | Where to get it |
|---|---|
| GitHub repo (with this code) | Already have it |
| Docker Hub account | https://hub.docker.com — sign up free |
| EC2 instance | AWS Console → EC2 → Ubuntu 22.04/24.04, `t2.micro`/`t3.micro` is enough |
| SSH key pair for EC2 | Created when launching the instance (the `.pem` file) |
| Security Group | Open **22 (SSH)** and **3000 (app)** to your IP / 0.0.0.0/0 |

---

## 2. One-time EC2 setup

1. SSH into the instance:
   ```bash
   ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
   ```
2. Clone your repo and run the bootstrap script (installs Docker + Compose plugin):
   ```bash
   git clone <your-repo-url> smartfarm && cd smartfarm
   bash deploy/ec2-setup.sh
   ```
3. Log out and back in (so the `docker` group applies), then verify:
   ```bash
   docker version
   docker compose version
   ```

That's it — the EC2 side is done. No manual `docker compose up` needed; CI/CD does it.

---

## 3. Create a Docker Hub access token

1. Docker Hub → **Account Settings → Security → New Access Token**.
2. Name it e.g. `github-actions`, grant **Read & Write**.
3. Copy the token (shown only once).

---

## 4. Add GitHub secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add all of these:

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | The access token from step 3 |
| `EC2_HOST` | EC2 public IP or DNS, e.g. `ec2-3-110-12-34.us-east-1.compute.amazonaws.com` |
| `EC2_USER` | `ubuntu` (default for Ubuntu AMIs) |
| `EC2_SSH_KEY` | Full content of your `.pem` file (paste as one block) |
| `MYSQL_ROOT_PASSWORD` | MySQL root password for production |
| `MYSQL_USERS_DB` | `smartfarm_users` |
| `MYSQL_FARMS_DB` | `smartfarm_farms` |
| `MONGODB_DATABASE` | `smartfarm_monitoring` |

> ⚠️ Keep `MYSQL_ROOT_PASSWORD` **alphanumeric only** (no `$`, quotes or spaces) —
> it is embedded in the `.env` file and the MySQL healthcheck command.

---

## 5. Push to main and watch the pipeline

```bash
git add -A && git commit -m "add CI/CD pipeline" && git push origin main
```

Open **Actions** tab in your repo. You'll see:

1. **CI** job → runs `pytest` for user/farm/monitoring/gateway services.
2. **CD** job → builds 4 images, pushes to Docker Hub (`latest` + commit SHA tags), then SSHes to EC2, pulls, and starts everything.

Verify on EC2:

```bash
docker ps                          # 6 containers running
docker compose -f docker-compose.prod.yaml logs -f   # watch logs
```

Then open **http://<EC2_PUBLIC_IP>:3000** in your browser — the Command Center dashboard should load.

---

## 6. How the files fit together

| File | Role |
|---|---|
| `.github/workflows/ci.yml` | Runs tests on every push/PR |
| `.github/workflows/cd.yml` | Build & push images to Docker Hub, then SSH-deploy to EC2 |
| `docker-compose.prod.yaml` | Production compose: pulls images, runs on EC2 (only port 3000 public) |
| `deploy/ec2-setup.sh` | One-time Docker installation on the EC2 instance |

### Security notes (prod vs local)

- In `docker-compose.prod.yaml` only **port 3000** is published. MySQL/MongoDB and the
  8001–8003 APIs stay on the private `smartfarm_net` network.
- Want to view service docs on EC2? Uncomment a `ports:` block (e.g. `8001:8001`)
  and re-push — or use an SSH tunnel instead:
  ```bash
  ssh -i key.pem -L 8001:localhost:8001 ubuntu@<EC2_IP>
  # then open http://localhost:8001/docs
  ```

---

## 7. Deploying a new version

Just push to `main` — the whole pipeline runs again. Images are versioned by
commit SHA (`:abc1234`), so you can roll back manually:

```bash
docker compose -f docker-compose.prod.yaml up -d --no-deps \
  --image youruser/smartfarm-user-service:abc1234 user-service
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `permission denied while trying to connect to the Docker daemon` | Log out/in so the `docker` group applies, or run `sudo usermod -aG docker ubuntu` and reconnect |
| CD fails with `Host key verification failed` | Add `fingerprint` to the ssh-action, or set `StrictHostKeyChecking=no` in your SSH config |
| App up but `http://IP:3000` doesn't load | Check Security Group has **3000** open, then `docker compose logs gateway-service` |
| DB schemas missing on fresh instance | Delete the volume (`docker volume rm` for mysql_data) and restart so `init-db/init.sql` re-runs |
| Healthchecks show degraded | `docker compose ps` — a service may still be starting; wait 60s+ (healthcheck interval is 60s) |