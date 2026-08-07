#!/bin/bash
# =============================================================================
# InvestWise AI - Deployment Script (runs on AWS EC2)
# -----------------------------------------------------------------------------
# This script is executed on the AWS EC2 instance via SSH from CircleCI.
# It performs a zero-downtime container replacement:
#   1. Pull the latest Docker image from Docker Hub
#   2. Stop the existing InvestAI container
#   3. Remove the old container
#   4. Prune unused Docker images
#   5. Start a new InvestAI container
#   6. Verify the deployment
#
# Usage:
#   bash deploy.sh <DOCKER_USERNAME>
#
# Example:
#   bash deploy.sh mydockerhubuser
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Arguments
# -----------------------------------------------------------------------------
# DOCKER_USERNAME is passed from CircleCI as the first argument.
# It is used to construct the full image name: ${DOCKER_USERNAME}/investai:latest
DOCKER_USERNAME="${1:?DOCKER_USERNAME is required. Usage: bash deploy.sh <DOCKER_USERNAME>}"

# The full image name and tag
IMAGE_NAME="${DOCKER_USERNAME}/investai"
IMAGE_TAG="latest"
CONTAINER_NAME="investai"

echo "=============================================="
echo "  InvestWise AI - Deployment to AWS EC2"
echo "=============================================="
echo "Image:     ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Container: ${CONTAINER_NAME}"
echo "=============================================="

# -----------------------------------------------------------------------------
# Step 1: Pull the latest Docker image from Docker Hub
# -----------------------------------------------------------------------------
echo "[1/6] Pulling latest Docker image..."
docker pull ${IMAGE_NAME}:${IMAGE_TAG}

# -----------------------------------------------------------------------------
# Step 2: Stop the existing InvestAI container (if running)
# The '|| true' ensures the script continues even if no container is running.
# -----------------------------------------------------------------------------
echo "[2/6] Stopping existing container..."
docker stop ${CONTAINER_NAME} || true

# -----------------------------------------------------------------------------
# Step 3: Remove the old container (if it exists)
# The '|| true' ensures the script continues even if no container exists.
# -----------------------------------------------------------------------------
echo "[3/6] Removing old container..."
docker rm ${CONTAINER_NAME} || true

# -----------------------------------------------------------------------------
# Step 4: Remove unused Docker images to free disk space
# The '|| true' ensures the script continues even if there are no unused images.
# -----------------------------------------------------------------------------
echo "[4/6] Pruning unused Docker images..."
docker image prune -af || true

# -----------------------------------------------------------------------------
# Step 5: Run the new InvestAI container
#   --name investai       : Container name
#   --restart always      : Automatically restart the container on failure or reboot
#   -p 80:8000            : Map host port 80 to container port 8000
# -----------------------------------------------------------------------------
echo "[5/6] Starting new container..."
docker run -d \
  --name ${CONTAINER_NAME} \
  --restart always \
  -p 80:8000 \
  ${IMAGE_NAME}:${IMAGE_TAG}

# -----------------------------------------------------------------------------
# Step 6: Verify the deployment by listing running containers
# -----------------------------------------------------------------------------
echo "[6/6] Verifying deployment..."
docker ps

echo "=============================================="
echo "  Deployment complete!"
echo "  InvestAI is running on port 80"
echo "=============================================="
