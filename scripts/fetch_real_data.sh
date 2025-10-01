#!/bin/bash

# AquaPredict - Fetch Real Data Script
# This script fetches actual satellite data from Google Earth Engine

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              🌍 AquaPredict - Fetch Real Data from GEE 🌍                    ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Configuration
START_DATE=${START_DATE:-"2023-01-01"}
END_DATE=${END_DATE:-"2023-12-31"}
OUTPUT_DIR="data/raw"
DATASET=${DATASET:-"all"}

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Start Date: $START_DATE"
echo "  End Date: $END_DATE"
echo "  Dataset: $DATASET"
echo "  Output Directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p $OUTPUT_DIR

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Earth Engine
if ! python3 -c "import ee" 2>/dev/null; then
    echo -e "${YELLOW}Installing Earth Engine API...${NC}"
    pip install earthengine-api
fi
echo -e "${GREEN}✓ Earth Engine API installed${NC}"

# Check GEE credentials
if [ ! -f "credentials/gee_key.json" ]; then
    echo -e "${RED}Error: GEE service account key not found${NC}"
    echo "Please place your service account key at: credentials/gee_key.json"
    echo ""
    echo "To create a service account:"
    echo "1. Go to: https://console.cloud.google.com"
    echo "2. Navigate to: IAM & Admin → Service Accounts"
    echo "3. Create service account with Earth Engine access"
    echo "4. Download JSON key"
    exit 1
fi
echo -e "${GREEN}✓ GEE credentials found${NC}"

# Test GEE connection
echo -e "\n${YELLOW}Testing Google Earth Engine connection...${NC}"
python3 << 'PYTHON_TEST'
import ee
import json
import sys

try:
    # Load credentials
    with open('credentials/gee_key.json') as f:
        credentials = json.load(f)
    
    # Initialize
    credentials_obj = ee.ServiceAccountCredentials(
        credentials['client_email'],
        'credentials/gee_key.json'
    )
    ee.Initialize(credentials_obj)
    
    # Test
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    size = chirps.size().getInfo()
    
    print(f"✓ Connected to Google Earth Engine!")
    print(f"  CHIRPS collection size: {size}")
    
except Exception as e:
    print(f"✗ Error connecting to GEE: {e}")
    sys.exit(1)
PYTHON_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to connect to Google Earth Engine${NC}"
    exit 1
fi

# Fetch data
echo -e "\n${YELLOW}Fetching real data from Google Earth Engine...${NC}"
echo "This may take 10-30 minutes depending on the date range."
echo ""

cd modules/data-ingestion

python3 main.py \
  --dataset $DATASET \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --output-dir ../../$OUTPUT_DIR \
  --format geotiff

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Data fetching completed successfully!${NC}"
    
    # List downloaded files
    echo -e "\n${YELLOW}Downloaded files:${NC}"
    ls -lh ../../$OUTPUT_DIR/
    
    # Upload to OCI Object Storage (if configured)
    if [ -f "../../.env" ] && grep -q "OCI_REGION" ../../.env; then
        echo -e "\n${YELLOW}Uploading to OCI Object Storage...${NC}"
        cd ../..
        
        python3 << 'PYTHON_UPLOAD'
import sys
sys.path.append('modules/common')
from oci_storage import DataStorageManager
import os
import glob

try:
    storage = DataStorageManager()
    
    files = glob.glob('data/raw/*.tif')
    
    for file_path in files:
        dataset_name = os.path.basename(file_path).replace('kenya_', '').replace('.tif', '')
        url = storage.save_raw_data(
            dataset_name=dataset_name,
            date='2023-01-01',
            file_path=file_path
        )
        print(f"✓ Uploaded: {file_path} → {url}")
    
    print("\n✓ All files uploaded to OCI Object Storage!")
    
except Exception as e:
    print(f"⚠️  Warning: Could not upload to OCI: {e}")
    print("   Files are still available locally in data/raw/")
PYTHON_UPLOAD
    fi
    
    # Summary
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                          ✓ Data Fetch Complete! ✓                           ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo "  1. Preprocess data:"
    echo "     cd modules/preprocessing && python main.py"
    echo ""
    echo "  2. Generate features:"
    echo "     cd modules/feature-engineering && python main.py --save-to-adb"
    echo ""
    echo "  3. Train models:"
    echo "     cd modules/modeling && python main.py --train"
    echo ""
    echo "  4. Start prediction service:"
    echo "     cd modules/prediction-service && uvicorn main:app --reload"
    echo ""
    
else
    echo -e "\n${RED}✗ Error during data fetching${NC}"
    exit 1
fi
