# 🚀 AquaPredict - Quick Start Guide

## **Get Started in 15 Minutes**

This guide will get you up and running with AquaPredict quickly, without complex Oracle setup initially.

---

## 📋 **Prerequisites**

```bash
# Check your system
python3 --version  # Should be 3.10+
node --version     # Should be 18+
docker --version   # Latest
git --version      # Latest
```

---

## 🎯 **Option 1: Local Development (Fastest)**

### **Step 1: Clone and Setup**

```bash
# Clone repository
git clone https://github.com/your-org/AquaPredict.git
cd AquaPredict

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **Step 2: Install OCI CLI (Simple Method)**

```bash
# Install via pip (easiest)
pip install oci-cli

# Verify
oci --version

# If that doesn't work, use our script
./scripts/install_oci_cli.sh
```

### **Step 3: Setup Google Earth Engine**

```bash
# Install Earth Engine
pip install earthengine-api

# Authenticate (opens browser)
earthengine authenticate

# This creates credentials at ~/.config/earthengine/credentials
```

### **Step 4: Configure Environment**

```bash
# Create .env file
cat > .env << 'EOF'
# Minimal configuration for local development

# Google Earth Engine (after authentication)
GEE_PROJECT_ID=your-project-id

# Local database (SQLite for testing)
DATABASE_URL=sqlite:///./aquapredict.db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

### **Step 5: Fetch Sample Data**

```bash
# Fetch 1 month of Kenya data (quick test)
cd modules/data-ingestion

python main.py \
  --dataset precipitation \
  --start-date 2023-01-01 \
  --end-date 2023-01-31 \
  --output-dir ../../data/raw

# This will take 5-10 minutes
```

### **Step 6: Start Backend API**

```bash
cd modules/prediction-service

# Start API (with sample data)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Open**: http://localhost:8000/docs

### **Step 7: Start Frontend**

```bash
# In a new terminal
cd modules/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Open**: http://localhost:3000

---

## 🐳 **Option 2: Docker (Recommended for Teams)**

### **Step 1: Clone Repository**

```bash
git clone https://github.com/your-org/AquaPredict.git
cd AquaPredict
```

### **Step 2: Configure Environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

### **Step 3: Start with Docker Compose**

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ☁️ **Option 3: Oracle Cloud (Production)**

### **Prerequisites**
- Oracle Cloud account
- OCI CLI installed
- Oracle ADB instance created

### **Quick Setup**

```bash
# 1. Install OCI CLI
pip install oci-cli

# 2. Configure OCI
oci setup config

# 3. Run Oracle setup script
./scripts/oracle_setup.sh

# Follow the prompts
```

**See**: [ORACLE_INTEGRATION_SUMMARY.md](ORACLE_INTEGRATION_SUMMARY.md) for detailed Oracle setup.

---

## 🧪 **Test Your Setup**

### **Test 1: API Health Check**

```bash
curl http://localhost:8000/health

# Expected: {"status": "healthy"}
```

### **Test 2: Make a Prediction**

```bash
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": -1.2921, "lon": 36.8219},
    "use_cached_features": false,
    "features": {
      "elevation": 1795,
      "slope": 5.2,
      "twi": 8.5,
      "precip_mean": 800,
      "temp_mean": 22.5
    }
  }'
```

### **Test 3: Frontend**

1. Open http://localhost:3000
2. Click on the map (Kenya region)
3. Click "Predict Aquifer"
4. See results!

---

## 🔧 **Common Issues & Fixes**

### **Issue 1: OCI CLI Installation Failed**

**Solution**:
```bash
# Use pip instead
pip install --user oci-cli

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Verify
oci --version
```

### **Issue 2: Earth Engine Authentication Failed**

**Solution**:
```bash
# Clear credentials
rm -rf ~/.config/earthengine

# Re-authenticate
earthengine authenticate

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### **Issue 3: Port Already in Use**

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### **Issue 4: Module Not Found**

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### **Issue 5: Frontend Won't Start**

**Solution**:
```bash
cd modules/frontend

# Clear cache
rm -rf .next node_modules package-lock.json

# Reinstall
npm install

# Start
npm run dev
```

---

## 📚 **Next Steps**

### **For Development**
1. ✅ Read [README.md](README.md) for full documentation
2. ✅ Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
3. ✅ Review code in `modules/` directory
4. ✅ Run tests: `pytest tests/ -v`

### **For Real Data**
1. ✅ Read [REAL_DATA_SETUP.md](REAL_DATA_SETUP.md)
2. ✅ Setup Google Earth Engine service account
3. ✅ Fetch Kenya data: `./scripts/fetch_real_data.sh`
4. ✅ Train models on real data

### **For Production**
1. ✅ Read [ORACLE_INTEGRATION_SUMMARY.md](ORACLE_INTEGRATION_SUMMARY.md)
2. ✅ Create Oracle Cloud account
3. ✅ Setup Oracle ADB and Object Storage
4. ✅ Deploy to OKE: `./scripts/deploy_oci.sh`

---

## 🎓 **Learning Path**

### **Week 1: Local Development**
- [ ] Setup local environment
- [ ] Fetch sample data
- [ ] Run API and frontend locally
- [ ] Make test predictions
- [ ] Understand code structure

### **Week 2: Real Data**
- [ ] Setup Google Earth Engine
- [ ] Fetch real Kenya data
- [ ] Process and generate features
- [ ] Train models
- [ ] Validate predictions

### **Week 3: Oracle Integration**
- [ ] Create Oracle Cloud account
- [ ] Setup Oracle ADB
- [ ] Setup OCI Object Storage
- [ ] Migrate data to Oracle
- [ ] Test end-to-end

### **Week 4: Production Deployment**
- [ ] Build Docker images
- [ ] Push to OCIR
- [ ] Deploy to OKE
- [ ] Configure monitoring
- [ ] Go live!

---

## 💡 **Pro Tips**

1. **Start Small**: Test with 1 month of data first
2. **Use Docker**: Easier for team collaboration
3. **Read Logs**: They tell you everything
4. **Test Often**: Run tests after each change
5. **Ask for Help**: Use GitHub Issues or Discussions

---

## 📞 **Get Help**

- **Documentation**: Check `docs/` directory
- **Issues**: https://github.com/your-org/AquaPredict/issues
- **Discussions**: https://github.com/your-org/AquaPredict/discussions
- **Email**: support@aquapredict.example.com

---

## ✅ **Checklist**

Before you start:
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Docker installed (optional)
- [ ] Git installed
- [ ] 8GB+ RAM available
- [ ] 20GB+ disk space

After setup:
- [ ] API running at http://localhost:8000
- [ ] Frontend running at http://localhost:3000
- [ ] Health check passes
- [ ] Test prediction works
- [ ] No errors in console

---

**You're ready to go! 🚀**

Choose your option above and start building!
