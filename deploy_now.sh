#!/bin/bash

# Quick deployment to 152.70.16.189
# This deploys the 4 core functionalities with simulated data

echo "🚀 Deploying AquaPredict to 152.70.16.189"

# Copy files to instance
echo "📦 Copying files..."
scp simple_api.py opc@152.70.16.189:~/
scp index.html opc@152.70.16.189:~/

# Setup and run
echo "🔧 Setting up on instance..."
ssh opc@152.70.16.189 << 'ENDSSH'
# Install dependencies
pip3 install fastapi uvicorn --user

# Stop any existing API
pkill -f "python3 simple_api.py" || true

# Start API
nohup python3 simple_api.py > api.log 2>&1 &

# Start simple HTTP server for frontend
pkill -f "python3 -m http.server" || true
nohup python3 -m http.server 3000 > frontend.log 2>&1 &

# Configure firewall
sudo firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
sudo firewall-cmd --permanent --add-port=3000/tcp 2>/dev/null || true
sudo firewall-cmd --reload 2>/dev/null || true

sleep 3

echo "✅ Deployment complete!"
echo ""
echo "API: http://152.70.16.189:8000"
echo "Frontend: http://152.70.16.189:3000"
echo ""
echo "Test API:"
echo "curl http://152.70.16.189:8000/health"
ENDSSH

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYED! Access your application:                      ║"
echo "║                                                              ║"
echo "║  🌐 Frontend: http://152.70.16.189:3000                     ║"
echo "║  📡 API: http://152.70.16.189:8000                          ║"
echo "║  📚 API Docs: http://152.70.16.189:8000/docs                ║"
echo "║                                                              ║"
echo "║  Features:                                                   ║"
echo "║  ✓ Probabilistic Aquifer Maps & Depth Bands                ║"
echo "║  ✓ Recharge/Depletion Forecasts                            ║"
echo "║  ✓ Sustainable Extraction Recommendations                   ║"
echo "║  ✓ ISO 14046 Water Stewardship Briefs                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  Don't forget to open ports 8000 and 3000 in OCI Security List!"
