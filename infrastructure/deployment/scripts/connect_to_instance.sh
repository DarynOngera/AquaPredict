#!/bin/bash

# Script to connect to private instances using OCI Bastion or port forwarding

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AquaPredict Instance Connection Helper ===${NC}"
echo ""

# Get instance IPs from terraform
cd "$(dirname "$0")/../../terraform"

BACKEND_IP=$(terraform state show module.compute.oci_core_instance.backend_api 2>/dev/null | grep "private_ip " | head -1 | awk '{print $3}' | tr -d '"')
PROCESSOR_IP=$(terraform state show module.compute.oci_core_instance.data_processor 2>/dev/null | grep "private_ip " | head -1 | awk '{print $3}' | tr -d '"')
LB_IP=$(terraform output -raw compute_load_balancer_ip 2>/dev/null)

echo "Infrastructure Details:"
echo "  Load Balancer: $LB_IP (public)"
echo "  Backend API:   $BACKEND_IP (private)"
echo "  Data Processor: $PROCESSOR_IP (private)"
echo ""

echo -e "${YELLOW}Since instances are in a private subnet, you have 3 options:${NC}"
echo ""
echo "1. Use OCI Console Bastion Service (Recommended)"
echo "   - Go to: https://cloud.oracle.com/bastion"
echo "   - Create a Bastion in your VCN's public subnet"
echo "   - Create SSH session to your instance"
echo ""
echo "2. Use OCI CLI to create port forwarding"
echo "   - Requires OCI CLI configured"
echo "   - We can set this up now"
echo ""
echo "3. Deploy via OCI Cloud Shell"
echo "   - Access instances from OCI Cloud Shell (has VCN access)"
echo ""

read -p "Choose option (1/2/3): " choice

case $choice in
  1)
    echo ""
    echo "Opening OCI Console Bastion page..."
    echo "Create a bastion, then create sessions to:"
    echo "  Backend: $BACKEND_IP"
    echo "  Processor: $PROCESSOR_IP"
    xdg-open "https://cloud.oracle.com/bastion" 2>/dev/null || open "https://cloud.oracle.com/bastion" 2>/dev/null || echo "Please open: https://cloud.oracle.com/bastion"
    ;;
    
  2)
    echo ""
    echo "Setting up OCI CLI port forwarding..."
    echo "This requires:"
    echo "  1. OCI CLI installed and configured"
    echo "  2. A bastion created in your compartment"
    echo ""
    read -p "Do you have OCI CLI configured? (y/n): " has_cli
    
    if [ "$has_cli" = "y" ]; then
      echo "Great! Let's create a bastion..."
      echo "Run these commands:"
      echo ""
      echo "# Get your compartment ID"
      echo "COMPARTMENT_ID=\$(terraform output -raw compartment_id)"
      echo ""
      echo "# Create bastion (one-time)"
      echo "oci bastion bastion create \\"
      echo "  --bastion-type STANDARD \\"
      echo "  --compartment-id \$COMPARTMENT_ID \\"
      echo "  --target-subnet-id <your-public-subnet-id> \\"
      echo "  --client-cidr-block-allow-list '[\"0.0.0.0/0\"]' \\"
      echo "  --name aquapredict-bastion"
    else
      echo "Please install OCI CLI first:"
      echo "  bash -c \"\$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)\""
    fi
    ;;
    
  3)
    echo ""
    echo -e "${GREEN}Using OCI Cloud Shell (Easiest Option!)${NC}"
    echo ""
    echo "1. Open OCI Console: https://cloud.oracle.com"
    echo "2. Click the Cloud Shell icon (>_) in the top right"
    echo "3. Upload your deployment scripts:"
    echo "   - setup_backend.sh"
    echo "   - setup_data_processor.sh"
    echo ""
    echo "4. From Cloud Shell, SSH directly to instances:"
    echo "   ssh -i ~/.ssh/id_rsa opc@$BACKEND_IP"
    echo "   ssh -i ~/.ssh/id_rsa opc@$PROCESSOR_IP"
    echo ""
    echo "5. Run the setup scripts on each instance"
    echo ""
    echo "Opening OCI Console..."
    xdg-open "https://cloud.oracle.com" 2>/dev/null || open "https://cloud.oracle.com" 2>/dev/null || echo "Please open: https://cloud.oracle.com"
    ;;
    
  *)
    echo "Invalid option"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}Next steps after connecting:${NC}"
echo "1. Copy deployment scripts to instance"
echo "2. Run: bash setup_backend.sh (or setup_data_processor.sh)"
echo "3. Configure OCI credentials"
echo "4. Test: curl http://localhost:8000/health"
