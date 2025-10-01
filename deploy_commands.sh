#!/bin/bash

# AquaPredict Deployment Commands
# Instance: 152.70.16.189
# User: opc

echo "🚀 Deploying AquaPredict to 152.70.16.189"

# Test SSH connection
echo "Testing SSH connection..."
ssh -o ConnectTimeout=10 opc@152.70.16.189 "echo '✅ SSH connection successful'"

if [ $? -eq 0 ]; then
    echo "✅ Connection verified!"
    echo ""
    echo "Next steps:"
    echo "1. Copy project to instance"
    echo "2. Install dependencies"
    echo "3. Setup and run"
else
    echo "❌ Cannot connect. Please check your SSH key."
    exit 1
fi
