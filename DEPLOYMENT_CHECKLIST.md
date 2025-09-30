# AquaPredict Deployment Checklist

## Pre-Deployment Checklist

### ✅ Prerequisites
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Docker & Docker Compose installed
- [ ] Git installed
- [ ] Google Earth Engine account created
- [ ] Oracle Cloud account created (for production)
- [ ] 8GB+ RAM available
- [ ] 20GB+ disk space available

### ✅ Credentials Setup
- [ ] GEE service account created
- [ ] GEE private key downloaded to `credentials/gee_key.json`
- [ ] Mapbox token obtained (for maps)
- [ ] OCI CLI configured (for production)
- [ ] `.env` file created from `.env.example`
- [ ] All environment variables filled in `.env`

### ✅ Local Development Setup
- [ ] Repository cloned
- [ ] Virtual environment created: `python3 -m venv venv`
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] Python dependencies installed: `pip install -r requirements.txt`
- [ ] Frontend dependencies installed: `cd modules/frontend && npm install`
- [ ] Data directories created: `mkdir -p data/{raw,processed,features}`
- [ ] Model directories created: `mkdir -p models/{trained,checkpoints}`
- [ ] GEE authenticated: `earthengine authenticate`

## Local Testing Checklist

### ✅ Module Testing
- [ ] Data ingestion tests pass: `pytest modules/data-ingestion/tests/ -v`
- [ ] Preprocessing tests pass: `pytest modules/preprocessing/tests/ -v`
- [ ] Feature engineering tests pass: `pytest modules/feature-engineering/tests/ -v`
- [ ] Modeling tests pass: `pytest modules/modeling/tests/ -v`
- [ ] Integration tests pass: `pytest tests/integration/ -v`
- [ ] All tests pass: `make test`
- [ ] Linting passes: `make lint`

### ✅ Data Pipeline Testing
- [ ] Sample data ingested: `make ingest-data`
- [ ] Data preprocessed: `make preprocess-data`
- [ ] Features generated: `make generate-features`
- [ ] Models trained: `make train-models`
- [ ] Models saved to `models/trained/`

### ✅ Service Testing
- [ ] Docker images built: `make build`
- [ ] Services started: `docker-compose up -d`
- [ ] Prediction service healthy: `curl http://localhost:8000/health`
- [ ] Frontend accessible: `http://localhost:3000`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] Airflow accessible: `http://localhost:8080` (admin/admin)
- [ ] Sample prediction works via API
- [ ] Sample prediction works via frontend

## Production Deployment Checklist (OCI)

### ✅ OCI Infrastructure Setup
- [ ] OCI account created and verified
- [ ] Compartment created for AquaPredict
- [ ] VCN and subnets configured
- [ ] Security lists and NSGs configured
- [ ] IAM policies created
- [ ] Terraform variables configured in `infrastructure/terraform/variables.tf`
- [ ] Terraform initialized: `cd infrastructure/terraform && terraform init`
- [ ] Terraform plan reviewed: `terraform plan`
- [ ] Infrastructure deployed: `terraform apply`

### ✅ OCI Resources Verification
- [ ] Autonomous Database created and running
- [ ] ADB wallet downloaded
- [ ] ADB connection tested
- [ ] OKE cluster created and running
- [ ] kubectl configured: `oci ce cluster create-kubeconfig`
- [ ] Object Storage buckets created
- [ ] Container Registry repositories created
- [ ] Data Science project created

### ✅ Application Deployment
- [ ] Docker images built: `./scripts/build_images.sh latest`
- [ ] Images tagged for OCIR
- [ ] Logged in to OCIR: `docker login <region>.ocir.io`
- [ ] Images pushed to OCIR: `./scripts/push_images.sh latest`
- [ ] Kubernetes namespace created: `kubectl apply -f infrastructure/k8s/namespace.yaml`
- [ ] Secrets created in Kubernetes
- [ ] Deployments applied: `kubectl apply -f infrastructure/k8s/deployments/`
- [ ] Services applied: `kubectl apply -f infrastructure/k8s/services/`
- [ ] Ingress configured: `kubectl apply -f infrastructure/k8s/ingress.yaml`
- [ ] Pods running: `kubectl get pods -n aquapredict`
- [ ] Services accessible: `kubectl get svc -n aquapredict`

### ✅ Post-Deployment Verification
- [ ] Health checks pass: `curl https://api.aquapredict.example.com/health`
- [ ] Frontend loads: `https://aquapredict.example.com`
- [ ] API documentation accessible: `https://api.aquapredict.example.com/docs`
- [ ] Sample prediction works in production
- [ ] Database connection verified
- [ ] Model loading verified
- [ ] Logs accessible: `kubectl logs -n aquapredict <pod-name>`
- [ ] Metrics collecting (Prometheus/Grafana)
- [ ] Alerts configured

### ✅ CI/CD Setup
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] GitHub Actions secrets configured:
  - [ ] `OCIR_REGION`
  - [ ] `OCIR_TENANCY`
  - [ ] `OCIR_USERNAME`
  - [ ] `OCIR_TOKEN`
  - [ ] `OCI_USER_OCID`
  - [ ] `OCI_TENANCY_OCID`
  - [ ] `OCI_REGION`
  - [ ] `OCI_FINGERPRINT`
  - [ ] `OCI_PRIVATE_KEY`
  - [ ] `OKE_CLUSTER_ID`
- [ ] CI/CD pipeline tested
- [ ] Automated tests running on PR
- [ ] Automated deployment on merge to main

## Monitoring & Maintenance Checklist

### ✅ Monitoring Setup
- [ ] Prometheus installed
- [ ] Grafana installed
- [ ] Dashboards created
- [ ] Alerts configured
- [ ] Log aggregation setup (OCI Logging)
- [ ] Error tracking configured
- [ ] Uptime monitoring configured

### ✅ Backup & DR
- [ ] ADB automatic backups enabled
- [ ] Object Storage cross-region replication enabled
- [ ] Kubernetes backup configured (Velero)
- [ ] DR region configured
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented

### ✅ Security
- [ ] SSL/TLS certificates configured
- [ ] Network security groups configured
- [ ] IAM policies reviewed and minimized
- [ ] Secrets stored in OCI Vault
- [ ] API authentication enabled
- [ ] Rate limiting configured
- [ ] Security scanning enabled
- [ ] Audit logging enabled

### ✅ Performance
- [ ] Auto-scaling configured for OKE nodes
- [ ] HPA configured for deployments
- [ ] ADB auto-scaling enabled
- [ ] CDN configured for frontend (optional)
- [ ] Caching configured (Redis)
- [ ] Database indexes optimized
- [ ] Load testing completed

## Documentation Checklist

### ✅ Documentation Complete
- [ ] README.md updated
- [ ] API documentation complete
- [ ] Architecture diagrams created
- [ ] Deployment guide updated
- [ ] User guide created
- [ ] Admin guide created
- [ ] Troubleshooting guide created
- [ ] Runbooks created for common tasks

## Training & Handoff Checklist

### ✅ Team Training
- [ ] Development team trained
- [ ] Operations team trained
- [ ] Support team trained
- [ ] Documentation reviewed with team
- [ ] Access credentials distributed
- [ ] On-call rotation established
- [ ] Escalation procedures documented

## Go-Live Checklist

### ✅ Final Verification
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Load testing passed
- [ ] User acceptance testing passed
- [ ] Stakeholder approval obtained
- [ ] Communication plan executed
- [ ] Rollback plan prepared
- [ ] Support team ready

### ✅ Launch
- [ ] DNS updated to production
- [ ] SSL certificates verified
- [ ] Monitoring active
- [ ] Alerts active
- [ ] Support channels open
- [ ] Launch announcement sent
- [ ] Post-launch monitoring (24-48 hours)

## Post-Launch Checklist

### ✅ Week 1
- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Gather user feedback
- [ ] Address critical issues
- [ ] Update documentation based on feedback

### ✅ Month 1
- [ ] Review metrics and KPIs
- [ ] Optimize performance
- [ ] Plan feature enhancements
- [ ] Review and update documentation
- [ ] Conduct retrospective

---

## Quick Reference

### Essential Commands

```bash
# Local Development
make setup                    # Initial setup
make deploy-local            # Start local services
make test                    # Run tests
make logs                    # View logs

# Data Pipeline
make ingest-data             # Fetch data from GEE
make preprocess-data         # Clean and normalize
make generate-features       # Compute features
make train-models            # Train ML models

# Production Deployment
./scripts/deploy_oci.sh      # Deploy to OCI
kubectl get pods -n aquapredict  # Check pod status
kubectl logs -f <pod-name> -n aquapredict  # View logs
```

### Important URLs

- **Local Frontend**: http://localhost:3000
- **Local API**: http://localhost:8000
- **Local API Docs**: http://localhost:8000/docs
- **Local Airflow**: http://localhost:8080
- **Production Frontend**: https://aquapredict.example.com
- **Production API**: https://api.aquapredict.example.com

### Support Contacts

- **Technical Issues**: GitHub Issues
- **OCI Support**: https://support.oracle.com
- **Documentation**: `docs/` directory

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
