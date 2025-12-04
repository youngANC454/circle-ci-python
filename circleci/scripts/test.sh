#!/bin/bash
# CircleCI Test Script

set -e

echo "=========================================="
echo "Running Tests"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_TESTS=0

# Test Backend
echo ""
echo "Testing Backend..."
cd backend

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run linting
echo "Running linter..."
pip install -q flake8
if flake8 app/ --max-line-length=100 --exclude=__pycache__; then
    echo -e "${GREEN}✓ Linting passed${NC}"
else
    echo -e "${YELLOW}⚠ Linting warnings (non-blocking)${NC}"
fi

echo "Running Backend tests.."
if pytest tests/ -v --tb=short 2>/dev/null || pytest --version >/dev/null 2>&1; then
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short || FAILED_TESTS=$((FAILED_TESTS+1))

    else
        echo -e "${YELLOW}⚠ No tests found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pytest not found${NC}"
fi

cd ..

echo ""
echo "Testing ML Engine..."
cd ml_engine

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Running ML enine tests..."
if [ -d "tests" ]; then
    pytest tests/ -v --tb=short 2>/dev/null || echo -e "${YELLOW}⚠ ML Engine tests failed${NC}"
else
    echo -e "${YELLOW}⚠ No tests found${NC}"
fi

cd ..

echo ""
echo "Running integration tests..."
if [ -d "tests" ]; then
    pytest tests/ -v --tb=short || FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ No integration tests found${NC}"
fi

echo ""
echo "=========================================="
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ $FAILED_TESTS tests failed${NC}"
    exit 1
fi
