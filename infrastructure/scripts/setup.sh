#!/bin/bash

# CI/CD AI Optimizer - Setup Script
# This script sets up the entire project

set -e

echo "=========================================="
echo "CI/CD AI Optimizer - Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p backend/app/{routes,services,utils}
mkdir -p ml_engine/{data/{raw,processed,models},notebooks,src/models}
mkdir -p monitoring/{prometheus/rules,grafana/{provisioning/{dashboards,datasources},dashboards}}
mkdir -p circleci/scripts
mkdir -p infrastructure/{docker/nginx,scripts,kubernetes}
mkdir -p tests

echo -e "${GREEN}✓ Directory structure created${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your CircleCI credentials${NC}"
    echo -e "${YELLOW}  Required: CIRCLECI_API_TOKEN, CIRCLECI_ORG_SLUG${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create .gitignore
echo ""
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Environment
.env
*.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# ML Models & Data
ml_engine/data/raw/*
ml_engine/data/processed/*
ml_engine/data/models/*.pkl
!ml_engine/data/.gitkeep

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Jupyter
.ipynb_checkpoints/

# Database
*.db
*.sqlite

# Prometheus & Grafana data
monitoring/grafana/data/
monitoring/prometheus/data/
EOF

echo -e "${GREEN}✓ .gitignore created${NC}"

# Create placeholder files for data directories
touch ml_engine/data/raw/.gitkeep
touch ml_engine/data/processed/.gitkeep
touch ml_engine/data/models/.gitkeep

# Create README
echo ""
echo "Creating README.md..."
cat > README.md << 'EOF'
# 🚀 CI/CD AI Optimizer

AI-Powered CI/CD Pipeline Optimizer with Infrastructure Monitoring

## 🎯 Features

- 🤖 AI-powered build failure prediction
- ⏱️ Build duration estimation
- 📊 Real-time infrastructure monitoring
- 📈 Beautiful Grafana dashboards
- 🔄 CircleCI integration
- 🐳 Fully Dockerized

## 🚀 Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and add your CircleCI credentials
3. Run setup: `./infrastructure/scripts/setup.sh`
4. Start services: `docker-compose up -d`
5. Access dashboards:
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - API Docs: http://localhost:8000/docs

## 📚 Documentation

See individual component READMEs for detailed documentation.

## 🛠️ Tech Stack

- Backend: FastAPI, Python
- ML: Scikit-learn, PyTorch
- Database: MongoDB
- Monitoring: Prometheus, Grafana
- CI/CD: CircleCI, Bazel
- Infrastructure: Docker, Kubernetes
EOF

echo -e "${GREEN}✓ README.md created${NC}"

# Set executable permissions on scripts
chmod +x infrastructure/scripts/*.sh 2>/dev/null || true

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your CircleCI credentials"
echo "2. Run: docker-compose up -d"
echo "3. Access Grafana at http://localhost:3000"
echo "4. Access API docs at http://localhost:8000/docs"
echo ""
echo "For more information, see README.md"
echo ""
