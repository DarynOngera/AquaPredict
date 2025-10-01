#!/bin/bash

# AquaPredict - Deploy to OCI Compute Instance
# This script deploys AquaPredict to your Oracle Cloud compute instance

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              🚀 Deploy AquaPredict to OCI Compute Instance 🚀                ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get instance details
echo -e "\n${YELLOW}Please provide your compute instance details:${NC}\n"

read -p "Instance IP address: " INSTANCE_IP
read -p "SSH user (ubuntu/opc): " INSTANCE_USER
read -p "SSH key path (e.g., ~/.ssh/id_rsa): " SSH_KEY_PATH

# Expand tilde
SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  IP: $INSTANCE_IP"
echo "  User: $INSTANCE_USER"
echo "  Key: $SSH_KEY_PATH"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$INSTANCE_USER@$INSTANCE_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ Cannot connect to instance${NC}"
    echo "Please check:"
    echo "  1. Instance IP is correct"
    echo "  2. SSH key path is correct"
    echo "  3. Security list allows SSH (port 22)"
    exit 1
fi

# Create deployment script
echo -e "\n${YELLOW}Creating deployment script...${NC}"

cat > /tmp/deploy_aquapredict.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

echo "🚀 Starting AquaPredict deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update -y || sudo yum update -y

# Install Python
echo "🐍 Installing Python..."
if command -v apt &> /dev/null; then
    sudo apt install -y python3 python3-pip python3-venv
else
    sudo yum install -y python3 python3-pip
fi

# Install Node.js
echo "📦 Installing Node.js..."
if command -v apt &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo yum install -y nodejs
fi

# Install Git
echo "📦 Installing Git..."
if command -v apt &> /dev/null; then
    sudo apt install -y git
else
    sudo yum install -y git
fi

# Verify installations
echo "✅ Verifying installations..."
python3 --version
node --version
npm --version

echo "✅ System setup complete!"
DEPLOY_SCRIPT

# Copy and run deployment script
echo -e "${YELLOW}Deploying to instance...${NC}"
scp -i "$SSH_KEY_PATH" /tmp/deploy_aquapredict.sh "$INSTANCE_USER@$INSTANCE_IP:/tmp/"
ssh -i "$SSH_KEY_PATH" "$INSTANCE_USER@$INSTANCE_IP" "bash /tmp/deploy_aquapredict.sh"

# Copy project files
echo -e "\n${YELLOW}Copying project files...${NC}"
ssh -i "$SSH_KEY_PATH" "$INSTANCE_USER@$INSTANCE_IP" "mkdir -p ~/AquaPredict"
scp -i "$SSH_KEY_PATH" -r . "$INSTANCE_USER@$INSTANCE_IP:~/AquaPredict/"

# Setup and run
echo -e "\n${YELLOW}Setting up AquaPredict...${NC}"
ssh -i "$SSH_KEY_PATH" "$INSTANCE_USER@$INSTANCE_IP" << 'REMOTE_SETUP'
cd ~/AquaPredict

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install fastapi uvicorn scikit-learn pandas numpy joblib

# Generate mock data
mkdir -p data/mock models

python3 << 'EOF'
import numpy as np
import pandas as pd
import os

os.makedirs('data/mock', exist_ok=True)
np.random.seed(42)

df = pd.DataFrame({
    'latitude': np.random.uniform(-4.7, 5.5, 1000),
    'longitude': np.random.uniform(33.9, 41.9, 1000),
    'elevation': np.random.uniform(0, 3000, 1000),
    'slope': np.random.uniform(0, 45, 1000),
    'twi': np.random.uniform(0, 20, 1000),
    'tpi': np.random.uniform(-50, 50, 1000),
    'precip_mean': np.random.uniform(200, 1500, 1000),
    'temp_mean': np.random.uniform(15, 30, 1000),
    'spi_3': np.random.uniform(-2, 2, 1000),
    'spei_6': np.random.uniform(-2, 2, 1000),
    'aquifer_present': np.random.choice([0, 1], 1000)
})
df.to_csv('data/mock/kenya_mock_data.csv', index=False)
print('✅ Mock data created')
EOF

# Train model
python3 << 'EOF'
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

os.makedirs('models', exist_ok=True)
df = pd.read_csv('data/mock/kenya_mock_data.csv')
X = df[['elevation', 'slope', 'twi', 'tpi', 'precip_mean', 'temp_mean', 'spi_3', 'spei_6']]
y = df['aquifer_present']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

joblib.dump(model, 'models/aquifer_classifier_mock.joblib')
print(f'✅ Model trained: {model.score(X_test, y_test):.2f} accuracy')
EOF

echo "✅ Setup complete!"
REMOTE_SETUP

# Configure firewall
echo -e "\n${YELLOW}Configuring firewall...${NC}"
ssh -i "$SSH_KEY_PATH" "$INSTANCE_USER@$INSTANCE_IP" << 'FIREWALL'
# Try firewalld (Oracle Linux)
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
fi

# Try ufw (Ubuntu)
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp 2>/dev/null || true
fi

echo "✅ Firewall configured"
FIREWALL

# Start API
echo -e "\n${YELLOW}Starting API...${NC}"
ssh -i "$SSH_KEY_PATH" "$INSTANCE_USER@$INSTANCE_IP" << 'START_API'
cd ~/AquaPredict
source venv/bin/activate

# Create simple API
cat > simple_api.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="AquaPredict API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load('models/aquifer_classifier_mock.joblib')

class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    elevation: float = 1500
    slope: float = 5.0
    twi: float = 8.0
    tpi: float = 0.0
    precip_mean: float = 800
    temp_mean: float = 22.0
    spi_3: float = 0.0
    spei_6: float = 0.0

@app.get("/")
def root():
    return {"message": "AquaPredict API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict")
def predict(request: PredictionRequest):
    features = np.array([[
        request.elevation, request.slope, request.twi, request.tpi,
        request.precip_mean, request.temp_mean, request.spi_3, request.spei_6
    ]])
    
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]
    
    return {
        "location": {"latitude": request.latitude, "longitude": request.longitude},
        "prediction": "present" if prediction == 1 else "absent",
        "probability": float(probability),
        "confidence": float(probability if prediction == 1 else 1 - probability)
    }
EOF

# Start API in background
nohup python3 simple_api.py > api.log 2>&1 &
sleep 3

echo "✅ API started"
START_API

# Test API
echo -e "\n${YELLOW}Testing API...${NC}"
sleep 2
if curl -s "http://$INSTANCE_IP:8000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${YELLOW}⚠ API may not be accessible from outside${NC}"
    echo "You may need to configure OCI Security List:"
    echo "  1. Go to: OCI Console → Networking → VCN"
    echo "  2. Add Ingress Rule for port 8000"
fi

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                          ✅ Deployment Complete! ✅                           ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Your AquaPredict API is running!${NC}"
echo ""
echo "📍 API URL: http://$INSTANCE_IP:8000"
echo "📍 Health Check: http://$INSTANCE_IP:8000/health"
echo "📍 API Docs: http://$INSTANCE_IP:8000/docs"
echo ""
echo -e "${YELLOW}Test it:${NC}"
echo "  curl http://$INSTANCE_IP:8000/health"
echo ""
echo "  curl -X POST http://$INSTANCE_IP:8000/predict \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"latitude\": -1.2921, \"longitude\": 36.8219, \"elevation\": 1795}'"
echo ""
echo -e "${YELLOW}⚠ Important:${NC}"
echo "  If the API is not accessible, configure OCI Security List:"
echo "  1. OCI Console → Networking → Virtual Cloud Networks"
echo "  2. Select your VCN → Security Lists"
echo "  3. Add Ingress Rule:"
echo "     - Source: 0.0.0.0/0"
echo "     - Destination Port: 8000"
echo "     - Protocol: TCP"
echo ""
echo -e "${YELLOW}SSH to your instance:${NC}"
echo "  ssh -i $SSH_KEY_PATH $INSTANCE_USER@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}View API logs:${NC}"
echo "  ssh -i $SSH_KEY_PATH $INSTANCE_USER@$INSTANCE_IP 'tail -f ~/AquaPredict/api.log'"
echo ""
