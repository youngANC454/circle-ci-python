#!/bin/bash

set -e

echo "Starting build process..."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "Building Backend..."

cd backend

docker build -t cicd-backend:${CIRCLE_SHA1:-latest} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend build successful${NC}"
else
    echo -e "${RED}✗ Backend build failed${NC}"
    exit 1
fi

cd ..

echo ""
echo "Building ML Engine..."
cd ml_engine

docker build -t cicd-ml-engine:${CIRCLE_SHA1:-latest} .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ML Engine build successful${NC}"
else
    echo -e "${RED}✗ ML Engine build failed${NC}"
    exit 1
fi

cd ..

echo ""
echo -e "${GREEN}✓ Build process completed successfully${NC}"

echo ""
echo "Tagging images..."
docker tag cicd-backend:${CIRCLE_SHA1:-latest} cicd-backend:latest
docker tag cicd-ml-engine:${CIRCLE_SHA1:-latest} cicd-ml-engine:latest

echo ""
echo "Builds Images:"
docker images | grep cicd-

echo ""
echo "Building Docker Complete..."
