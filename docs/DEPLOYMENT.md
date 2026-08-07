# InvestWise AI - Deployment Guide

This document describes the CI/CD pipeline and deployment process for the
InvestWise AI backend application running on AWS EC2.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Updated Project Structure (Deployment Files)](#updated-project-structure-deployment-files)
- [CI/CD Pipeline Flow](#cicd-pipeline-flow)
- [CircleCI Environment Variables](#circleci-environment-variables)
- [AWS EC2 Prerequisites](#aws-ec2-prerequisites)
- [Docker Hub Setup](#docker-hub-setup)
- [Verification Commands](#verification-commands)
- [Manual Redeployment](#manual-redeployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The deployment uses a **single-container** approach:

- **GitHub** hosts the source code and triggers the pipeline on every push to `main`.
- **CircleCI** builds the Docker image, pushes it to Docker Hub, and deploys to EC2.
- **Docker Hub** stores the container image (`${DOCKER_USERNAME}/investai:latest`).
- **AWS EC2** runs the container, exposing the application on port 80.

The Docker image is built from the existing `docker/Dockerfile.backend`, which
runs the Django backend with Gunicorn on port 8000. The container maps host
port 80 to container port 8000.

---

## Architecture

```
Developer
    │
git push origin main
    │
    ▼
GitHub Repository
    │
    ▼
CircleCI
    │
    ├── Checkout repository
    ├── Build Docker image (docker/Dockerfile.backend)
    ├── Tag image (${DOCKER_USERNAME}/investai:latest)
    ├── Login to Docker Hub
    ├── Push image to Docker Hub
    ├── SSH into AWS EC2
    ├── Pull latest Docker image
    ├── Stop existing InvestAI container
    ├── Remove old container
    ├── Remove unused images
    ├── Run new InvestAI container
    ├── Verify deployment (docker ps)
    ▼
InvestAI running on AWS EC2 (port 80 → 8000)
```

---

## Updated Project Structure (Deployment Files)

Only deployment-related files are included below. Application source code is
**not** modified.

```
InvestWise-AI/
├── .circleci/
│   └── config.yml          # CircleCI CI/CD pipeline configuration
├── deploy.sh               # EC2 deployment script (pull, stop, remove, run)
├── docker/
│   ├── Dockerfile.backend  # Backend Dockerfile (unchanged, used for build)
│   ├── Dockerfile.frontend # Frontend Dockerfile (unchanged)
│   ├── Dockerfile.ai       # AI service Dockerfile (unchanged)
│   ├── Dockerfile.celery   # Celery worker Dockerfile (unchanged)
│   ├── nginx.conf          # NGINX configuration (unchanged)
│   └── nginx-frontend.conf # NGINX frontend configuration (unchanged)
├── docker-compose.yml      # Development compose (unchanged)
├── docker-compose.prod.yml # Production compose (unchanged)
├── docs/
│   └── DEPLOYMENT.md       # This deployment documentation
├── README.md               # Project README (unchanged)
└── ...                     # Application source code (unchanged)
```

---

## CI/CD Pipeline Flow

### 1. Trigger

The pipeline is triggered automatically when code is pushed to the `main`
branch:

```bash
git push origin main
```

### 2. Build

CircleCI checks out the repository and builds the Docker image using the
existing `docker/Dockerfile.backend`:

```bash
docker build -f docker/Dockerfile.backend -t ${DOCKER_USERNAME}/investai:latest .
```

Docker layer caching is enabled via `setup_remote_docker` with
`docker_layer_caching: true` for faster rebuilds.

### 3. Push to Docker Hub

The image is tagged as `${DOCKER_USERNAME}/investai:latest` and pushed to
Docker Hub:

```bash
docker login -u "${DOCKER_USERNAME}" --password-stdin
docker push ${DOCKER_USERNAME}/investai:latest
```

### 4. Deploy to AWS EC2

CircleCI copies `deploy.sh` to the EC2 instance via SCP and executes it over
SSH. The `deploy.sh` script performs the following on the EC2 instance:

```bash
docker pull ${DOCKER_USERNAME}/investai:latest
docker stop investai || true
docker rm investai || true
docker image prune -af || true
docker run -d \
  --name investai \
  --restart always \
  -p 80:8000 \
  ${DOCKER_USERNAME}/investai:latest
docker ps
```

### 5. Verify

The pipeline verifies the deployment by running `docker ps` on the EC2
instance to confirm the container is running.

---

## CircleCI Environment Variables

All secrets must be configured as **CircleCI Environment Variables** in the
project settings (Project Settings → Environment Variables).

| Variable           | Description                                      | Example                  |
| ------------------ | ------------------------------------------------ | ------------------------ |
| `DOCKER_USERNAME`  | Docker Hub username                              | `mydockerhubuser`        |
| `DOCKER_PASSWORD`  | Docker Hub password or access token              | `ghp_xxxxxxxxxxxx`       |
| `EC2_HOST`         | Public IP address or DNS of the AWS EC2 instance | `3.120.0.10`             |
| `EC2_USER`         | SSH user for the EC2 instance                    | `ec2-user` or `ubuntu`   |
| `EC2_SSH_KEY`      | Private SSH key (contents of `.pem` file)        | `-----BEGIN OPENSSH...`  |

### How to Set Environment Variables in CircleCI

1. Go to your project in [CircleCI](https://app.circleci.com/).
2. Navigate to **Project Settings** → **Environment Variables**.
3. Add each variable listed above.
4. **Important:** For `EC2_SSH_KEY`, paste the **entire contents** of your
   private key file (e.g., `my-key.pem`), including the `-----BEGIN...` and
   `-----END...` lines.

---

## AWS EC2 Prerequisites

Before deploying, ensure the EC2 instance meets the following requirements:

### 1. Operating System

- **Amazon Linux 2** or **Ubuntu 22.04 LTS** (recommended)

### 2. Docker

Docker must be installed and running on the EC2 instance:

```bash
# Check Docker installation
docker --version

# If not installed, install Docker:
# Ubuntu:
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Amazon Linux 2:
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo systemctl enable docker
```

### 3. Docker Permissions

The SSH user must be able to run Docker commands without `sudo`:

```bash
sudo usermod -aG docker ${USER}
# Log out and log back in for the group change to take effect
```

### 4. Security Group

The EC2 security group must allow inbound traffic on port 80 (HTTP):

| Type       | Protocol | Port | Source       |
| ---------- | -------- | ---- | ------------ |
| HTTP       | TCP      | 80   | 0.0.0.0/0    |
| SSH        | TCP      | 22   | Your IP      |

### 5. SSH Key Pair

- Generate or use an existing SSH key pair.
- The **private key** must be stored as the `EC2_SSH_KEY` CircleCI environment
  variable.
- The **public key** must be added to `~/.ssh/authorized_keys` on the EC2
  instance.

```bash
# On your local machine, generate a new key pair (if needed):
ssh-keygen -t ed25519 -f ~/.ssh/investai-deploy -N ""

# Copy the public key to the EC2 instance:
ssh-copy-id -i ~/.ssh/investai-deploy.pub ${EC2_USER}@${EC2_HOST}

# The private key contents go into CircleCI as EC2_SSH_KEY:
cat ~/.ssh/investai-deploy
```

### 6. Application Environment Variables (Optional)

The backend application reads configuration from environment variables. If
you need to pass secrets (e.g., `DJANGO_SECRET_KEY`, `DATABASE_URL`, API keys),
you can either:

- **Option A:** Pass them via `docker run -e` in `deploy.sh` (modify the
  `docker run` command to include `-e VAR=value`).
- **Option B:** Create an `.env` file on the EC2 instance and reference it
  with `--env-file`.

The application falls back to SQLite if `DATABASE_URL` is not set, so it can
run without an external database for basic operation.

---

## Docker Hub Setup

1. Create a [Docker Hub](https://hub.docker.com/) account (if you don't have
   one).
2. Create an **access token** (recommended over password):
   - Go to **Account Settings** → **Security** → **New Access Token**.
   - Name it `investai-circleci`.
   - Copy the token and use it as the `DOCKER_PASSWORD` environment variable.
3. (Optional) Create a repository named `investai` under your Docker Hub
   account. The image will be pushed to
   `${DOCKER_USERNAME}/investai:latest`.

---

## Verification Commands

### Check if the container is running

```bash
# SSH into the EC2 instance
ssh -i /path/to/key.pem ${EC2_USER}@${EC2_HOST}

# List running containers
docker ps

# Expected output should include:
# CONTAINER ID   IMAGE                              ...   PORTS                  NAMES
# ...            ${DOCKER_USERNAME}/investai:latest ...   0.0.0.0:80->8000/tcp   investai
```

### Check container logs

```bash
docker logs -f investai
```

### Test the application endpoint

```bash
curl http://localhost/api/health/
# or
curl http://${EC2_HOST}/api/health/
```

### Check container resource usage

```bash
docker stats investai
```

---

## Manual Redeployment

If you need to redeploy manually (without pushing to GitHub), follow these
steps:

### Option 1: Run deploy.sh directly on EC2

```bash
# SSH into the EC2 instance
ssh -i /path/to/key.pem ${EC2_USER}@${EC2_HOST}

# Run the deployment script
bash /tmp/deploy.sh ${DOCKER_USERNAME}
```

### Option 2: Run the commands manually

```bash
# SSH into the EC2 instance
ssh -i /path/to/key.pem ${EC2_USER}@${EC2_HOST}

# Pull the latest image
docker pull ${DOCKER_USERNAME}/investai:latest

# Stop and remove the old container
docker stop investai || true
docker rm investai || true

# Prune unused images
docker image prune -af || true

# Start the new container
docker run -d \
  --name investai \
  --restart always \
  -p 80:8000 \
  ${DOCKER_USERNAME}/investai:latest

# Verify
docker ps
```

### Option 3: Rebuild and push from local machine

```bash
# Build the image
docker build -f docker/Dockerfile.backend -t ${DOCKER_USERNAME}/investai:latest .

# Login to Docker Hub
docker login -u "${DOCKER_USERNAME}" --password-stdin

# Push to Docker Hub
docker push ${DOCKER_USERNAME}/investai:latest

# Then run deploy.sh on EC2 (Option 1 or 2 above)
```

---

## Troubleshooting

### Container fails to start

```bash
# Check logs
docker logs investai

# Check if the container is running
docker ps -a
```

### Port 80 already in use

```bash
# Check what's using port 80
sudo lsof -i :80

# Stop the conflicting process or container
docker stop investai
docker rm investai
```

### Docker permission denied

```bash
# Ensure the SSH user is in the docker group
sudo usermod -aG docker ${USER}
# Log out and log back in
```

### SSH connection issues

- Verify the EC2 security group allows inbound SSH (port 22).
- Verify the `EC2_SSH_KEY` environment variable contains the correct private
  key.
- Verify the `EC2_HOST` and `EC2_USER` are correct.

### CircleCI pipeline fails

- Check the CircleCI job logs in the CircleCI web UI.
- Verify all environment variables are set correctly.
- Verify the Dockerfile path (`docker/Dockerfile.backend`) is correct.
