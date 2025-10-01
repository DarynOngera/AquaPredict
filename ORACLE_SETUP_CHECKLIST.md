# 🔧 Oracle Cloud Setup - Information Needed

## 📋 **Information I Need From You**

Please provide the following details from your Oracle Cloud instance:

---

## 1️⃣ **Oracle Autonomous Database (ADB) Information**

### **From OCI Console → Autonomous Database → Your Database**

```bash
# Database Details
DB_NAME=                    # e.g., "aquapredict"
DB_DISPLAY_NAME=            # e.g., "AquaPredict-DB"
DB_OCID=                    # Starts with: ocid1.autonomousdatabase.oc1...

# Connection Information
DB_SERVICE_NAME=            # e.g., "aquapredict_high" or "aquapredict_low"
DB_USERNAME=admin           # Default is "admin"
DB_PASSWORD=                # The password you set during creation

# Wallet Information
WALLET_DOWNLOADED=          # yes/no - Did you download the wallet?
WALLET_PASSWORD=            # Password you set for the wallet
WALLET_LOCATION=            # Where you saved wallet.zip (e.g., ~/Downloads/wallet.zip)
```

**How to find this**:
1. Go to: OCI Console → Oracle Database → Autonomous Database
2. Click on your database name
3. Copy the OCID from the database details page
4. Click "DB Connection" to download wallet

---

## 2️⃣ **OCI Account Information**

### **From OCI Console → Profile → Tenancy**

```bash
# Tenancy Details
TENANCY_NAME=               # Your tenancy name
TENANCY_OCID=               # Starts with: ocid1.tenancy.oc1...
REGION=                     # e.g., "us-ashburn-1", "uk-london-1"

# User Details
USER_OCID=                  # Your user OCID (starts with: ocid1.user.oc1...)
USER_EMAIL=                 # Your email address

# Compartment
COMPARTMENT_NAME=           # e.g., "AquaPredict" or "root"
COMPARTMENT_OCID=           # Starts with: ocid1.compartment.oc1...
```

**How to find this**:
1. Click your profile icon (top right)
2. Click "Tenancy: <your-tenancy-name>"
3. Copy the OCIDs from the tenancy details page

---

## 3️⃣ **OCI Object Storage (If Created)**

```bash
# Bucket Names (if you created them)
BUCKET_RAW_DATA=            # e.g., "aquapredict-data-raw"
BUCKET_PROCESSED=           # e.g., "aquapredict-data-processed"
BUCKET_MODELS=              # e.g., "aquapredict-models"
BUCKET_REPORTS=             # e.g., "aquapredict-reports"

# Namespace
NAMESPACE=                  # Auto-generated, find in: Object Storage → Buckets
```

**How to find this**:
1. Go to: Storage → Object Storage → Buckets
2. The namespace is shown at the top of the page

---

## 4️⃣ **OCI API Key (For CLI/SDK)**

```bash
# API Key Information
API_KEY_FINGERPRINT=        # e.g., "12:34:56:78:90:ab:cd:ef..."
API_PRIVATE_KEY_PATH=       # Path to your private key file (e.g., ~/.oci/oci_api_key.pem)
```

**If you haven't created an API key yet**:
1. Go to: Profile → User Settings → API Keys
2. Click "Add API Key"
3. Download the private key
4. Save it to: `~/.oci/oci_api_key.pem`
5. Copy the fingerprint

---

## 5️⃣ **Network Information (Optional)**

```bash
# VCN Details (if you created a custom VCN)
VCN_NAME=                   # Virtual Cloud Network name
VCN_OCID=                   # VCN OCID
SUBNET_OCID=                # Subnet OCID
```

---

## 📝 **Quick Copy Template**

Copy this and fill in your values:

```bash
# ============================================
# ORACLE CLOUD CONFIGURATION
# ============================================

# Autonomous Database
export DB_NAME="aquapredict"
export DB_SERVICE_NAME="aquapredict_high"
export DB_USERNAME="admin"
export DB_PASSWORD="YOUR_DB_PASSWORD_HERE"
export WALLET_PASSWORD="YOUR_WALLET_PASSWORD_HERE"
export WALLET_LOCATION="./credentials/wallet"

# OCI Account
export TENANCY_OCID="ocid1.tenancy.oc1..YOUR_TENANCY_OCID"
export USER_OCID="ocid1.user.oc1..YOUR_USER_OCID"
export REGION="us-ashburn-1"
export COMPARTMENT_OCID="ocid1.compartment.oc1..YOUR_COMPARTMENT_OCID"

# API Key
export API_KEY_FINGERPRINT="YOUR_FINGERPRINT_HERE"
export API_PRIVATE_KEY_PATH="~/.oci/oci_api_key.pem"

# Object Storage (optional)
export NAMESPACE="YOUR_NAMESPACE"
export BUCKET_RAW_DATA="aquapredict-data-raw"
export BUCKET_MODELS="aquapredict-models"
```

---

## 🎯 **What I'll Do With This Information**

Once you provide the above, I will:

1. ✅ Create your `.env` file with correct values
2. ✅ Create OCI CLI config file (`~/.oci/config`)
3. ✅ Set up wallet connection
4. ✅ Test database connectivity
5. ✅ Create Object Storage buckets (if needed)
6. ✅ Load database schema
7. ✅ Test end-to-end connection
8. ✅ Provide you with working commands

---

## 🚀 **Immediate Next Steps**

### **Step 1: Download Wallet**

If you haven't already:

1. Go to your ADB instance in OCI Console
2. Click "DB Connection"
3. Click "Download Wallet"
4. Set a wallet password (remember this!)
5. Save `wallet.zip` to your computer

### **Step 2: Move Wallet to Project**

```bash
cd /home/ongera/projects/AquaPredict

# Create credentials directory
mkdir -p credentials/wallet

# Copy wallet.zip to project (update path to your download location)
cp ~/Downloads/wallet.zip credentials/

# Extract wallet
unzip credentials/wallet.zip -d credentials/wallet/

# Verify
ls credentials/wallet/
# Should see: cwallet.sso, tnsnames.ora, sqlnet.ora, etc.
```

### **Step 3: Provide Information**

Reply with the filled template above, and I'll configure everything for you!

---

## 📸 **Screenshots That Would Help**

If you can provide screenshots of:
1. ✅ ADB instance details page
2. ✅ Tenancy details page
3. ✅ Object Storage buckets page (if created)

This will help me ensure everything is configured correctly.

---

## ⚠️ **Security Note**

**DO NOT share**:
- ❌ Your actual passwords
- ❌ Private key contents
- ❌ Wallet files

**DO share**:
- ✅ OCIDs (these are safe to share)
- ✅ Region names
- ✅ Bucket names
- ✅ Service names
- ✅ Fingerprints

I'll create template files with placeholders, and you can fill in the sensitive values locally.

---

## 💡 **Quick Test**

While I wait for your information, you can test if your ADB is accessible:

```bash
# If you have SQL*Plus installed
sqlplus admin/<your-password>@<service-name>

# Example:
# sqlplus admin/MyPassword123@aquapredict_high
```

If this connects, your database is ready! ✅

---

**Reply with the information above, and I'll get you configured immediately!** 🚀
