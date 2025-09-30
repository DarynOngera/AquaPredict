# AquaPredict OCI Deployment

Infrastructure as Code for deploying AquaPredict on Oracle Cloud Infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        OCI Tenancy                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Compartment: AquaPredict                 │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   OKE        │  │   ADB        │  │  Object      │    │ │
│  │  │  Cluster     │  │  (Spatial)   │  │  Storage     │    │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │ │
│  │         │                  │                  │            │ │
│  │  ┌──────┴──────────────────┴──────────────────┴────────┐  │ │
│  │  │              Load Balancer                           │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │  Data Science│  │  Model       │  │  Container   │    │ │
│  │  │  Notebooks   │  │  Deployment  │  │  Registry    │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- OCI Account with appropriate permissions
- OCI CLI installed and configured
- Terraform >= 1.5
- kubectl >= 1.28
- Docker
- Helm >= 3.12

## Quick Start

### 1. Configure OCI CLI

```bash
oci setup config
```

### 2. Set Environment Variables

```bash
export TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..xxx"
export TF_VAR_user_ocid="ocid1.user.oc1..xxx"
export TF_VAR_fingerprint="xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
export TF_VAR_private_key_path="~/.oci/oci_api_key.pem"
export TF_VAR_region="us-ashburn-1"
export TF_VAR_compartment_ocid="ocid1.compartment.oc1..xxx"
```

### 3. Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### 4. Configure kubectl

```bash
oci ce cluster create-kubeconfig \
  --cluster-id <cluster-ocid> \
  --file ~/.kube/config \
  --region us-ashburn-1
```

### 5. Deploy Applications

```bash
cd infrastructure/k8s
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployments/
kubectl apply -f services/
kubectl apply -f ingress.yaml
```

## Components

### 1. Oracle Autonomous Database (ADB)

**Purpose**: Store spatial data, features, predictions

**Configuration**:
- **Type**: Autonomous Data Warehouse
- **Version**: 19c with Spatial
- **Storage**: 1 TB (auto-scaling)
- **Compute**: 2 OCPUs (auto-scaling)
- **Network**: Private endpoint in VCN

**Setup**:
```bash
# Create ADB instance
terraform apply -target=module.adb

# Download wallet
oci db autonomous-database generate-wallet \
  --autonomous-database-id <adb-ocid> \
  --file wallet.zip \
  --password <password>

# Create schema
sqlplus admin/<password>@aquapredict_high @sql/schema.sql
```

### 2. Oracle Kubernetes Engine (OKE)

**Purpose**: Host containerized services

**Configuration**:
- **Kubernetes Version**: 1.28
- **Node Pool**: 3 nodes (VM.Standard.E4.Flex, 2 OCPUs, 16GB RAM each)
- **Auto-scaling**: 3-10 nodes
- **Network**: Private subnet

**Services Deployed**:
- Prediction Service (FastAPI)
- Frontend (Next.js)
- Airflow (Scheduler, Webserver, Workers)

### 3. Object Storage

**Purpose**: Store raw data, models, reports

**Buckets**:
- `aquapredict-data-raw`: Raw GEE data
- `aquapredict-data-processed`: Processed features
- `aquapredict-models`: Trained models
- `aquapredict-reports`: Generated reports

### 4. OCI Data Science

**Purpose**: Model training and experimentation

**Configuration**:
- **Notebook Session**: VM.Standard2.4 (4 OCPUs, 60GB RAM)
- **Block Storage**: 100 GB
- **Conda Environment**: Python 3.10 with ML libraries

### 5. OCI Model Deployment

**Purpose**: Scalable model inference

**Configuration**:
- **Instance**: VM.Standard2.2 (2 OCPUs, 30GB RAM)
- **Auto-scaling**: 1-5 instances
- **Load Balancer**: Integrated

### 6. Container Registry (OCIR)

**Purpose**: Store Docker images

**Images**:
- `aquapredict/data-ingestion:latest`
- `aquapredict/preprocessing:latest`
- `aquapredict/feature-engineering:latest`
- `aquapredict/prediction-service:latest`
- `aquapredict/frontend:latest`

## Deployment Steps

### Phase 1: Infrastructure Setup

```bash
# 1. Create VCN and subnets
terraform apply -target=module.network

# 2. Create ADB
terraform apply -target=module.adb

# 3. Create OKE cluster
terraform apply -target=module.oke

# 4. Create Object Storage buckets
terraform apply -target=module.object_storage

# 5. Create Container Registry repositories
terraform apply -target=module.ocir
```

### Phase 2: Build and Push Images

```bash
# Login to OCIR
docker login <region>.ocir.io

# Build images
./scripts/build_images.sh

# Push images
./scripts/push_images.sh
```

### Phase 3: Deploy Applications

```bash
# Create namespace
kubectl create namespace aquapredict

# Create secrets
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=<password> \
  -n aquapredict

# Deploy services
kubectl apply -f k8s/deployments/ -n aquapredict
kubectl apply -f k8s/services/ -n aquapredict
kubectl apply -f k8s/ingress.yaml -n aquapredict
```

### Phase 4: Configure Monitoring

```bash
# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  -n monitoring --create-namespace

# Install Grafana
helm install grafana grafana/grafana \
  -n monitoring
```

## Kubernetes Resources

### Prediction Service Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prediction-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prediction-service
  template:
    metadata:
      labels:
        app: prediction-service
    spec:
      containers:
      - name: api
        image: <region>.ocir.io/<tenancy>/aquapredict/prediction-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prediction-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prediction-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## CI/CD with OCI DevOps

### Build Pipeline

```yaml
# build_spec.yaml
version: 0.1
component: build
timeoutInSeconds: 600
shell: bash

steps:
  - type: Command
    name: "Build Docker Image"
    command: |
      docker build -t prediction-service:${OCI_BUILD_RUN_ID} .
      
  - type: Command
    name: "Push to OCIR"
    command: |
      docker tag prediction-service:${OCI_BUILD_RUN_ID} \
        ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:${OCI_BUILD_RUN_ID}
      docker push ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:${OCI_BUILD_RUN_ID}

outputArtifacts:
  - name: docker_image
    type: DOCKER_IMAGE
    location: ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:${OCI_BUILD_RUN_ID}
```

### Deployment Pipeline

```yaml
# deployment_spec.yaml
version: 0.1
component: deployment
environment: production

steps:
  - type: Command
    name: "Update Kubernetes Deployment"
    command: |
      kubectl set image deployment/prediction-service \
        api=${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:${OCI_BUILD_RUN_ID} \
        -n aquapredict
      
  - type: Command
    name: "Wait for Rollout"
    command: |
      kubectl rollout status deployment/prediction-service -n aquapredict
```

## Monitoring and Logging

### OCI Logging

```bash
# Enable logging for OKE
oci logging log create \
  --log-group-id <log-group-ocid> \
  --display-name oke-cluster-logs \
  --log-type SERVICE \
  --configuration '{"source":{"service":"oke","resource":"<cluster-ocid>"}}'
```

### Prometheus Metrics

```yaml
# ServiceMonitor for prediction service
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: prediction-service
spec:
  selector:
    matchLabels:
      app: prediction-service
  endpoints:
  - port: metrics
    interval: 30s
```

## Cost Optimization

1. **Auto-scaling**: Enable for OKE nodes and ADB
2. **Spot Instances**: Use for non-critical workloads
3. **Reserved Capacity**: For production workloads
4. **Storage Tiering**: Move old data to Archive Storage
5. **Resource Tagging**: Track costs by component

## Security

1. **Network Security**: Private subnets, security lists, NSGs
2. **IAM Policies**: Least privilege access
3. **Secrets Management**: OCI Vault for sensitive data
4. **Encryption**: At-rest and in-transit encryption
5. **Audit Logging**: Enable for all resources

## Backup and DR

1. **ADB Backups**: Automatic daily backups (retained 60 days)
2. **Object Storage**: Cross-region replication
3. **Kubernetes**: Velero for cluster backups
4. **DR Region**: Secondary region for failover

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n aquapredict
kubectl describe pod <pod-name> -n aquapredict
kubectl logs <pod-name> -n aquapredict
```

### Check Service Endpoints

```bash
kubectl get svc -n aquapredict
kubectl get ingress -n aquapredict
```

### Database Connection

```bash
# Test connection
sqlplus admin/<password>@aquapredict_high

# Check spatial features
SELECT * FROM USER_SDO_GEOM_METADATA;
```

## Scaling

### Scale Deployment

```bash
kubectl scale deployment prediction-service --replicas=5 -n aquapredict
```

### Scale Node Pool

```bash
oci ce node-pool update \
  --node-pool-id <pool-ocid> \
  --size 5
```

## Maintenance

### Update Application

```bash
# Rolling update
kubectl set image deployment/prediction-service \
  api=<new-image> -n aquapredict

# Rollback if needed
kubectl rollout undo deployment/prediction-service -n aquapredict
```

### Update Kubernetes

```bash
# Upgrade cluster
oci ce cluster update \
  --cluster-id <cluster-ocid> \
  --kubernetes-version v1.29.0
```

## Support

- **Documentation**: https://docs.oracle.com/en-us/iaas/
- **Support**: https://support.oracle.com/
- **Community**: https://community.oracle.com/
