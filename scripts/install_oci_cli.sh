#!/bin/bash

# AquaPredict - Install OCI CLI (Alternative Method)
# This script installs OCI CLI using pip instead of the installer script

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                    Installing Oracle Cloud CLI                              ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${YELLOW}Method 1: Install via pip (Recommended)${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Install OCI CLI via pip
echo -e "\n${YELLOW}Installing OCI CLI...${NC}"
pip install --user oci-cli

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ OCI CLI installed successfully!${NC}"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "\n${YELLOW}Adding OCI CLI to PATH...${NC}"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
        echo -e "${GREEN}✓ PATH updated${NC}"
    fi
    
    # Verify installation
    echo -e "\n${YELLOW}Verifying installation...${NC}"
    oci --version
    
    echo -e "\n${GREEN}✓ OCI CLI is ready to use!${NC}"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "  1. Configure OCI CLI:"
    echo "     oci setup config"
    echo ""
    echo "  2. Or run the Oracle setup script:"
    echo "     ./scripts/oracle_setup.sh"
    echo ""
else
    echo -e "\n${RED}✗ Installation failed${NC}"
    echo -e "\n${YELLOW}Alternative: Install using system package manager${NC}"
    echo ""
    echo "For Debian/Ubuntu:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install python3-pip"
    echo "  pip3 install oci-cli"
    echo ""
    echo "For macOS:"
    echo "  brew install oci-cli"
    echo ""
    exit 1
fi
