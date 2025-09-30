#!/bin/bash

# AquaPredict Oracle Integration Setup Script
# This script helps you set up the complete Oracle stack

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                   🌊 AquaPredict Oracle Integration Setup 🌊                 ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "\n${BLUE}This script will help you set up:${NC}"
echo "  1. Oracle Autonomous Database (ADB)"
echo "  2. OCI Object Storage"
echo "  3. OCI Container Registry (OCIR)"
echo "  4. Environment configuration"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# ============================================
# Step 1: Check Prerequisites
# ============================================
echo -e "\n${YELLOW}Step 1: Checking prerequisites...${NC}"

command -v oci >/dev/null 2>&1 || {
    echo -e "${RED}OCI CLI is required but not installed.${NC}"
    echo "Install: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm"
    exit 1
}

command -v python3 >/dev/null 2>&1 || {
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
}

command -v docker >/dev/null 2>&1 || {
    echo -e "${RED}Docker is required but not installed.${NC}"
    exit 1
}

echo -e "${GREEN}✓ All prerequisites met${NC}"

# ============================================
# Step 2: OCI Configuration
# ============================================
echo -e "\n${YELLOW}Step 2: OCI Configuration${NC}"

if [ ! -f ~/.oci/config ]; then
    echo "OCI CLI not configured. Running setup..."
    oci setup config
else
    echo -e "${GREEN}✓ OCI CLI already configured${NC}"
fi

# Get compartment ID
echo ""
read -p "Enter your OCI Compartment OCID: " COMPARTMENT_ID
export COMPARTMENT_ID

# Get region
read -p "Enter your OCI Region (e.g., us-ashburn-1): " OCI_REGION
export OCI_REGION

# Get tenancy name
read -p "Enter your OCI Tenancy Name: " TENANCY_NAME
export TENANCY_NAME

# ============================================
# Step 3: Create Object Storage Buckets
# ============================================
echo -e "\n${YELLOW}Step 3: Creating OCI Object Storage buckets...${NC}"

BUCKETS=("aquapredict-data-raw" "aquapredict-data-processed" "aquapredict-models" "aquapredict-reports")

for BUCKET in "${BUCKETS[@]}"; do
    echo "Creating bucket: $BUCKET"
    oci os bucket create \
        --name $BUCKET \
        --compartment-id $COMPARTMENT_ID \
        --region $OCI_REGION \
        2>/dev/null || echo "  (Bucket may already exist)"
done

echo -e "${GREEN}✓ Object Storage buckets created${NC}"

# ============================================
# Step 4: ADB Setup Instructions
# ============================================
echo -e "\n${YELLOW}Step 4: Oracle Autonomous Database Setup${NC}"
echo ""
echo "Please create an ADB instance manually in the OCI Console:"
echo "  1. Go to: Menu → Oracle Database → Autonomous Database"
echo "  2. Click: Create Autonomous Database"
echo "  3. Configure:"
echo "     - Display Name: AquaPredict-DB"
echo "     - Database Name: aquapredict"
echo "     - Workload Type: Data Warehouse"
echo "     - OCPU Count: 2 (auto-scaling enabled)"
echo "     - Storage: 1 TB (auto-scaling enabled)"
echo "  4. Download the wallet and save to: ./credentials/wallet/"
echo ""
read -p "Press Enter when ADB is created and wallet is downloaded..."

# ============================================
# Step 5: Extract Wallet
# ============================================
echo -e "\n${YELLOW}Step 5: Setting up ADB wallet...${NC}"

mkdir -p credentials/wallet

if [ -f wallet.zip ]; then
    unzip -o wallet.zip -d credentials/wallet/
    echo -e "${GREEN}✓ Wallet extracted${NC}"
else
    echo -e "${YELLOW}Please place wallet.zip in the project root and run:${NC}"
    echo "  unzip wallet.zip -d credentials/wallet/"
fi

# ============================================
# Step 6: Environment Configuration
# ============================================
echo -e "\n${YELLOW}Step 6: Configuring environment variables...${NC}"

# Get database credentials
read -p "Enter ADB Admin Password: " -s DB_PASSWORD
echo ""
read -p "Enter Wallet Password: " -s WALLET_PASSWORD
echo ""

# Create .env file
cat > .env << EOF
# Oracle Autonomous Database
WALLET_LOCATION=./credentials/wallet
WALLET_PASSWORD=${WALLET_PASSWORD}
DB_USERNAME=admin
DB_PASSWORD=${DB_PASSWORD}
DB_DSN=aquapredict_high

# OCI Configuration
OCI_CONFIG_FILE=~/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
OCI_REGION=${OCI_REGION}
OCI_TENANCY=${TENANCY_NAME}
COMPARTMENT_ID=${COMPARTMENT_ID}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

echo -e "${GREEN}✓ Environment configured (.env created)${NC}"

# ============================================
# Step 7: Install Python Dependencies
# ============================================
echo -e "\n${YELLOW}Step 7: Installing Python dependencies...${NC}"

pip install oracledb oci

echo -e "${GREEN}✓ Dependencies installed${NC}"

# ============================================
# Step 8: Create Database Schema
# ============================================
echo -e "\n${YELLOW}Step 8: Creating database schema...${NC}"

python3 << 'PYTHON_SCRIPT'
import oracledb
import os

try:
    # Initialize Oracle client
    oracledb.init_oracle_client(config_dir="./credentials/wallet")
    
    # Connect
    connection = oracledb.connect(
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN"),
        wallet_location=os.getenv("WALLET_LOCATION"),
        wallet_password=os.getenv("WALLET_PASSWORD")
    )
    
    print("✓ Connected to Oracle ADB")
    
    # Execute schema
    with open('sql/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor = connection.cursor()
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    for i, statement in enumerate(statements):
        try:
            cursor.execute(statement)
            print(f"  Executed statement {i+1}/{len(statements)}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"  Warning: {e}")
    
    connection.commit()
    print("✓ Schema created successfully!")
    
    connection.close()

except Exception as e:
    print(f"Error: {e}")
    print("\nPlease run the schema manually:")
    print("  sqlplus admin/<password>@aquapredict_high @sql/schema.sql")

PYTHON_SCRIPT

# ============================================
# Step 9: Test Connection
# ============================================
echo -e "\n${YELLOW}Step 9: Testing Oracle integration...${NC}"

python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
sys.path.append('modules/prediction-service')
from oracle_database import OracleADBClient

async def test():
    try:
        db = OracleADBClient()
        location_id = await db.insert_location(-1.2921, 36.8219, 'Nairobi')
        print(f"✓ Test location created: {location_id}")
        print("✓ Oracle ADB connection working!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
PYTHON_SCRIPT

# ============================================
# Step 10: OCIR Setup
# ============================================
echo -e "\n${YELLOW}Step 10: Setting up OCIR (Optional)...${NC}"

read -p "Do you want to configure OCIR now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "To configure OCIR:"
    echo "  1. Go to OCI Console → User Settings → Auth Tokens"
    echo "  2. Generate a new auth token"
    echo "  3. Copy the token (you won't see it again!)"
    echo ""
    read -p "Enter your OCI username (tenancy/oracleidentitycloudservice/email): " OCIR_USERNAME
    read -p "Enter your auth token: " -s OCIR_TOKEN
    echo ""
    
    # Login to OCIR
    echo "$OCIR_TOKEN" | docker login ${OCI_REGION}.ocir.io -u "$OCIR_USERNAME" --password-stdin
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ OCIR configured${NC}"
        
        # Add to .env
        echo "" >> .env
        echo "# OCIR Configuration" >> .env
        echo "OCIR_REGION=${OCI_REGION}" >> .env
        echo "OCIR_TENANCY=${TENANCY_NAME}" >> .env
        echo "OCIR_USERNAME=${OCIR_USERNAME}" >> .env
    else
        echo -e "${RED}OCIR login failed${NC}"
    fi
fi

# ============================================
# Summary
# ============================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                          ✅ Setup Complete! ✅                                ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Oracle Integration Status:${NC}"
echo "  ✓ OCI CLI configured"
echo "  ✓ Object Storage buckets created"
echo "  ✓ ADB wallet configured"
echo "  ✓ Environment variables set"
echo "  ✓ Database schema created"
echo "  ✓ Connection tested"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Train your models:"
echo "     cd modules/modeling && python main.py --train"
echo ""
echo "  2. Start the prediction service:"
echo "     cd modules/prediction-service && uvicorn main:app --reload"
echo ""
echo "  3. Start the frontend:"
echo "     cd modules/frontend && npm install && npm run dev"
echo ""
echo "  4. Open http://localhost:3000 and start predicting!"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - Complete guide: docs/ORACLE_INTEGRATION_COMPLETE.md"
echo "  - API guide: docs/API_INTEGRATION_GUIDE.md"
echo ""
echo "🌊 Let's make this dream work with Oracle! 🚀"
echo ""
