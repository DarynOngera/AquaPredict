#!/bin/bash

# AquaPredict Backend Startup Script
# Starts the backend service with proper configuration

set -e

echo "🚀 Starting AquaPredict Backend..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials before continuing.${NC}"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models data credentials logs

# Check if models exist
if [ ! -f models/aquifer_classifier.pkl ] && [ ! -f models/recharge_forecaster.pkl ]; then
    echo -e "${YELLOW}⚠️  No models found in models/ directory${NC}"
    echo -e "${YELLOW}   Backend will use heuristic-based predictions${NC}"
    echo -e "${YELLOW}   To add trained models from Colab:${NC}"
    echo -e "${YELLOW}   1. Copy .pkl files to models/ directory${NC}"
    echo -e "${YELLOW}   2. Restart the backend${NC}"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"

# Navigate to backend directory
cd modules/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check GEE credentials
if [ -f "../../credentials/gee_key.json" ]; then
    echo -e "${GREEN}✅ GEE credentials found${NC}"
else
    echo -e "${YELLOW}⚠️  GEE credentials not found${NC}"
    echo -e "${YELLOW}   Backend will use simulated data fallback${NC}"
fi

# Start the backend
echo -e "${GREEN}🎯 Starting backend server...${NC}"
echo ""
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
