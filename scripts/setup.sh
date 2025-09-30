#!/bin/bash

# AquaPredict Setup Script
# This script sets up the development environment

set -e

echo "=========================================="
echo "AquaPredict Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Setup data directories
echo -e "\n${YELLOW}Creating data directories...${NC}"
mkdir -p data/{raw,processed,features,cache}
mkdir -p models/{trained,checkpoints}
mkdir -p reports/generated
mkdir -p logs

echo -e "${GREEN}✓ Directories created${NC}"

# Copy environment template
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your credentials${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Setup frontend
echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd modules/frontend
npm install
cd ../..

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# GEE Authentication
echo -e "\n${YELLOW}Google Earth Engine Authentication${NC}"
echo "Please run: earthengine authenticate"
echo "Follow the browser prompts to authenticate"

# Summary
echo -e "\n=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Authenticate with Google Earth Engine: earthengine authenticate"
echo "3. Start services: docker-compose up -d"
echo "4. Access frontend: http://localhost:3000"
echo "5. Access API docs: http://localhost:8000/docs"
echo ""
echo "For more information, see README.md"
echo ""
