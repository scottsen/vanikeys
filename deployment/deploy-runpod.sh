#!/bin/bash
# VaniKeys RunPod Deployment Script
#
# This script builds and pushes the VaniKeys Docker image to a registry
# for use with RunPod Serverless.
#
# Usage:
#   ./deploy-runpod.sh [docker-username] [version-tag]
#
# Example:
#   ./deploy-runpod.sh scottsen latest
#   ./deploy-runpod.sh scottsen v0.2.0

set -euo pipefail

# Configuration
DOCKER_USERNAME="${1:-scottsen}"
VERSION_TAG="${2:-latest}"
IMAGE_NAME="vanikeys-runpod"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   VaniKeys RunPod Deployment                  ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "Image: ${YELLOW}${FULL_IMAGE_NAME}${NC}"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Verify we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Are you in the VaniKeys root directory?${NC}"
    exit 1
fi

# Step 1: Run tests
echo -e "${YELLOW}Step 1: Running tests...${NC}"
if pytest tests/ -v --tb=short; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed. Fix tests before deploying.${NC}"
    exit 1
fi
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
echo "This may take 3-5 minutes (downloading base image, installing dependencies)"

if docker build -t "${FULL_IMAGE_NAME}" -f deployment/Dockerfile .; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi
echo ""

# Step 3: Test image locally
echo -e "${YELLOW}Step 3: Testing image locally...${NC}"
echo "Verifying VaniKeys can import successfully..."

if docker run --rm "${FULL_IMAGE_NAME}" python -c "
from vanikeys.crypto import generate_master_seed, seed_to_keypair_at_path
from vanikeys.crypto.fingerprint import compute_ssh_fingerprint
from vanikeys.matchers import MultiSubstringMatcher
seed = generate_master_seed()
priv, pub = seed_to_keypair_at_path(seed, 0)
fp = compute_ssh_fingerprint(pub)
print('✓ VaniKeys import test passed')
print(f'  Sample fingerprint: {fp}')
"; then
    echo -e "${GREEN}✓ Image verification passed${NC}"
else
    echo -e "${RED}✗ Image verification failed${NC}"
    exit 1
fi
echo ""

# Step 4: Push to Docker registry
echo -e "${YELLOW}Step 4: Pushing to Docker Hub...${NC}"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""
echo "Ensure you're logged in: docker login"
echo ""

read -p "Push image to Docker Hub? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if docker push "${FULL_IMAGE_NAME}"; then
        echo -e "${GREEN}✓ Image pushed successfully${NC}"
    else
        echo -e "${RED}✗ Docker push failed. Are you logged in? (docker login)${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping push. You can push later with:${NC}"
    echo "  docker push ${FULL_IMAGE_NAME}"
fi
echo ""

# Success summary
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Deployment Complete                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Docker image: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo ""
echo "Next steps:"
echo "  1. Go to https://www.runpod.io/console/serverless"
echo "  2. Click 'New Endpoint'"
echo "  3. Configure:"
echo "     - Name: vanikeys-gacha"
echo "     - GPU: RTX 4090 (best cost/performance)"
echo "     - Container Image: ${FULL_IMAGE_NAME}"
echo "     - Container Disk: 10GB"
echo "     - Workers: Min 0, Max 10"
echo "     - Idle Timeout: 5 seconds"
echo "  4. Deploy and get your endpoint ID"
echo "  5. Test with deployment/test_runpod.py"
echo ""
echo "Documentation: docs/SERVERLESS_GPU_OPTIONS.md"
