# 🖥️ AquaPredict - Compute Instance Setup

## **You Have: Oracle Cloud Compute Instance (VM)**

Perfect! We can run AquaPredict directly on your compute instance. This is actually simpler than the full Oracle stack.

---

## 📋 **Information I Need**

### **1. Compute Instance Details**

```bash
# Instance Information
INSTANCE_IP=                # Public IP address (e.g., 123.45.67.89)
INSTANCE_USER=              # Usually "ubuntu" or "opc"
SSH_KEY_PATH=               # Path to your SSH private key (e.g., ~/.ssh/id_rsa)

# Instance Specs
INSTANCE_SHAPE=             # e.g., VM.Standard.E4.Flex
INSTANCE_OCPUS=             # Number of OCPUs (e.g., 2)
INSTANCE_MEMORY_GB=         # Memory in GB (e.g., 16)
INSTANCE_OS=                # e.g., "Ubuntu 22.04", "Oracle Linux 8"
```

**How to find this**:
1. Go to: OCI Console → Compute → Instances
2. Click on your instance
3. Copy the Public IP address
4. Note the shape and OS

---

## 🚀 **Quick Setup Options**

### **Option 1: Simple Setup (Recommended)**

Run everything directly on the compute instance with SQLite (no Oracle ADB needed).

**Advantages**:
- ✅ No additional Oracle services needed
- ✅ No wallet configuration
- ✅ Faster to set up
- ✅ Lower cost
- ✅ Good for development/testing

**What you'll have**:
- FastAPI backend running on port 8000
- Next.js frontend running on port 3000
- SQLite database (local file)
- Mock data for testing

---

### **Option 2: Full Setup**

Add Oracle ADB later when you need production features.

**Advantages**:
- ✅ Start simple, scale later
- ✅ Can add Oracle ADB anytime
- ✅ Can add Object Storage anytime

---

## 🎯 **Let's Get Started - Simple Setup**

### **Step 1: Connect to Your Instance**

```bash
# From your local machine
ssh -i <your-ssh-key> <user>@<instance-ip>

# Example:
# ssh -i ~/.ssh/oci_key ubuntu@123.45.67.89
```

**Provide me with**:
- Your instance IP: `_______________`
- Your SSH user (ubuntu/opc): `_______________`
- Can you connect successfully? (yes/no): `_______________`

---

### **Step 2: Install Dependencies on Instance**

Once connected, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y  # For Ubuntu
# OR
sudo yum update -y  # For Oracle Linux

# Install Python 3.10+
sudo apt install python3 python3-pip python3-venv -y  # Ubuntu
# OR
sudo yum install python3 python3-pip -y  # Oracle Linux

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y  # Ubuntu
# OR
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install nodejs -y  # Oracle Linux

# Install Git
sudo apt install git -y  # Ubuntu
# OR
sudo yum install git -y  # Oracle Linux

# Verify installations
python3 --version  # Should be 3.10+
node --version     # Should be 18+
npm --version
git --version
```

---

### **Step 3: Clone Project to Instance**

```bash
# On your compute instance
cd ~
git clone https://github.com/your-org/AquaPredict.git
cd AquaPredict

# Or if you're developing locally, copy files:
# From your local machine:
# scp -i ~/.ssh/oci_key -r /home/ongera/projects/AquaPredict ubuntu@<instance-ip>:~/
```

---

### **Step 4: Quick Start with Mock Data**

```bash
# On your compute instance
cd ~/AquaPredict

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install fastapi uvicorn scikit-learn pandas numpy joblib sqlalchemy

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
```

---

### **Step 5: Create Simple API**

```bash
# Create simple API file
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

# Load model
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Run API in background
nohup python3 simple_api.py > api.log 2>&1 &

# Check if running
curl http://localhost:8000/health
```

---

### **Step 6: Configure Firewall**

```bash
# Open port 8000 for API
sudo firewall-cmd --permanent --add-port=8000/tcp  # Oracle Linux
sudo firewall-cmd --reload

# OR for Ubuntu
sudo ufw allow 8000/tcp
sudo ufw enable
```

**Also in OCI Console**:
1. Go to: Networking → Virtual Cloud Networks
2. Click your VCN → Security Lists
3. Add Ingress Rule:
   - Source: 0.0.0.0/0
   - Destination Port: 8000
   - Protocol: TCP

---

### **Step 7: Test from Your Machine**

```bash
# From your local machine
curl http://<instance-ip>:8000/health

# Test prediction
curl -X POST "http://<instance-ip>:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -1.2921,
    "longitude": 36.8219,
    "elevation": 1795,
    "slope": 5.2,
    "twi": 8.5
  }'
```

---

## 🎯 **What You'll Have**

After completing the above:
- ✅ API running on your compute instance
- ✅ Accessible at: `http://<your-ip>:8000`
- ✅ Working predictions with mock data
- ✅ No Oracle ADB needed (using SQLite)
- ✅ Ready for frontend integration

---

## 📊 **System Architecture (Simplified)**

```
Your Compute Instance (OCI)
├── FastAPI Backend (Port 8000)
│   ├── ML Model (Random Forest)
│   ├── SQLite Database (local)
│   └── Mock Data
│
└── (Optional) Next.js Frontend (Port 3000)
```

---

## 🔄 **Next Steps**

### **Option A: Add Frontend**

```bash
# On compute instance
cd ~/AquaPredict/modules/frontend
npm install
npm run build
npm start  # Runs on port 3000

# Open firewall for port 3000
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### **Option B: Keep It Simple**

Just use the API directly:
- Test with curl
- Build a simple HTML page
- Use Postman for testing

### **Option C: Add Oracle ADB Later**

When you're ready:
1. Create Autonomous Database
2. Download wallet
3. Update connection strings
4. Migrate from SQLite to Oracle

---

## 💡 **Cost Optimization**

**Current Setup Cost**:
- Compute Instance: ~$50-100/month (depending on shape)
- No additional Oracle services
- **Total**: ~$50-100/month

**To reduce costs**:
- Use smaller instance shape
- Stop instance when not in use
- Use Oracle Free Tier (if eligible)

---

## 🚨 **Security Checklist**

- [ ] Change default passwords
- [ ] Configure firewall rules
- [ ] Use SSH keys (not passwords)
- [ ] Keep system updated
- [ ] Enable HTTPS (later)
- [ ] Restrict API access (later)

---

## 📝 **Information Template**

Please provide:

```bash
# Your Compute Instance
INSTANCE_IP=                # e.g., 123.45.67.89
INSTANCE_USER=              # ubuntu or opc
SSH_KEY_PATH=               # Path to your SSH key

# Instance Specs
INSTANCE_SHAPE=             # e.g., VM.Standard.E4.Flex
INSTANCE_OS=                # Ubuntu 22.04 or Oracle Linux 8

# Can you SSH into it?
SSH_WORKS=                  # yes/no
```

---

**Once you provide this information, I'll give you the exact commands to run!** 🚀

**What's your instance IP and can you SSH into it?**
