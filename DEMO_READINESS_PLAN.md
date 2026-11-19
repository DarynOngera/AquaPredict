# AquaPredict: End-to-End Demo Readiness Plan

## Goal

Deliver a stable public demo in the next few days using a single, tested
application path:

```text
Browser -> Next.js frontend -> /api reverse proxy -> FastAPI backend -> local demo model artifacts
```

The demo must clearly label simulated, estimated, or live data. It must not
claim that an unavailable GEE or Oracle integration is live.

## Scope Decision

Use the current implementation under `modules/frontend` and `modules/backend`.
Use the three checked-in `model_artifacts/*.joblib` files only for the
precipitation prediction flow. Defer OKE, Terraform, Airflow, data ingestion,
and the legacy `modules/prediction-service` stack until after the demo.

The aquifer classifier can be trained from the reproducible synthetic-label
pipeline in `modules/backend/train_demo_aquifer_model.py`. Its model and
metadata are explicitly demonstration-only, not ground-truth validated.

## Phase 0 — Secure the repository (first)

1. Treat values in the tracked `infrastructure/terraform/terraform.tfvars` as
   exposed credentials.
2. Rotate OCI API credentials, database passwords, GEE credentials, and any
   associated SSH key if they were real values.
3. Replace that file with `terraform.tfvars.example`, remove the real file from
   Git tracking, and store environment-specific values in the deployment
   platform's secret store.
4. Schedule a separate, coordinated Git-history rewrite after the demo. Do not
   rewrite shared history during the demo stabilization window.

**Acceptance criterion:** no secrets or real deployment configuration are
committed in the demo branch.

## Phase 1 — Make one canonical application path

1. Add a `docker-compose.demo.yml` containing only:
   - `backend` built from `modules/backend`
   - `frontend` built from `modules/frontend`
   - a reverse proxy exposing the frontend and forwarding `/api` to backend
2. Remove the nonexistent `frontend -> prediction-service` dependency from the
   demo configuration.
3. Do not build orchestration/reporting services: their Dockerfiles are absent.
4. Change the frontend's API configuration to `NEXT_PUBLIC_API_URL=/api` at
   image-build time. Do not use `REACT_APP_API_URL`.
5. Copy or mount `model_artifacts/` into the backend image at the path used by
   `app/services/model_service.py`.
6. Add `/ready` to the backend and make `/health` report model and fallback
   status without logging environment values.
7. Restrict CORS to the demo domain(s) if frontend and API are not served from
   the same origin.

**Acceptance criterion:** `docker compose -f docker-compose.demo.yml config`
passes, images build, and the browser can access frontend and backend through
one public origin.

## Phase 2 — Make the product behavior honest and predictable

1. In the prediction panel, label each source:
   - Precipitation: `Trained demo model` when an artifact is loaded.
   - Aquifer/recharge: `Estimated demo result` unless their named models are
     supplied and validated.
   - Data: `Live`, `Simulated`, or `Fallback estimate` based on the response.
2. Keep the precipitation tab as the model-backed feature for the demo. It
   calls `/api/inference/predict` and defaults to `random_forest`.
3. Disable or clearly badge Oracle dashboards when database access is absent;
   avoid seeded statistics presented as live figures.
4. Add visible error messages for unavailable predictions rather than only
   console errors.
5. Remove startup prints of Oracle username/DSN and password-state metadata.

**Acceptance criterion:** every result shown during the rehearsal identifies
whether it came from a trained model, simulated data, or a fallback estimate.

## Phase 3 — Verify the exact deployed behavior

1. Add smoke tests that run against the built demo stack:
   - frontend returns HTTP 200;
   - `/api/health` returns healthy;
   - `/api/inference/predict` succeeds with `random_forest`;
   - requesting an unknown model returns a useful 400 response;
   - the aquifer and recharge routes return a source label.
2. Add a model-load check that fails the demo build if no `*.joblib` artifact
   is present in the backend container.
3. Verify the frontend build has no `localhost:8000` API endpoint baked in.
4. Replace the broken CI matrix with checks that match the canonical frontend
   and backend, plus the demo smoke tests.
5. Rehearse the demo from a fresh browser session on the deployed host.

**Acceptance criterion:** a clean deployment succeeds twice in succession and
the scripted demo works without manual server intervention.

## Phase 4 — Deploy and freeze

1. Prefer one existing/new OCI Compute VM with Docker Compose and Nginx/Caddy;
   this is lower risk than repairing OKE and Terraform before the demo.
2. Configure HTTPS and a public hostname. Use a pinned image tag based on the
   commit SHA, not `latest`.
3. Save a rollback command that restores the previous known-good image tag.
4. Prepare an offline fallback: a local Compose deployment and a brief screen
   recording of the core prediction flow.
5. Freeze code after final rehearsal except for demo-blocking fixes.

## Credentials and access needed

Do **not** paste secrets into chat, source files, or Git. Add them directly to
the target host's secret manager/environment file, or share access through the
approved deployment channel.

### Required for a public deployment

- Target choice: existing Compute VM or permission to create a new one.
- Hostname/domain and DNS access, or approval to demo by IP temporarily.
- SSH deployment access for the selected VM (a deploy key or an account with
  the required access).
- OCI tenancy/compartment access only if a new VM, public IP, or DNS resource
  must be created.

### Required for live satellite-backed aquifer/recharge features

- GEE project ID with Earth Engine enabled.
- GEE service-account email and its JSON private-key file, stored outside the
  repository as `credentials/gee_key.json` (or in the configured credential
  directory).
- Confirmation that the service account is authorized to use the GEE project.

### Optional — not required for the core model demo

- Oracle database connection details and wallet: only if the Oracle dashboard
  must use genuine data.
- Mapbox token: not needed for the current map, which uses public OSM/Esri
  tile layers.

## Out of scope until after the demo

- Repairing OKE manifests and image registry automation.
- Deploying Airflow, ingestion, preprocessing, feature engineering, or
  reporting services.
- Retraining models or claiming validation metrics not supplied with the
  artifacts.
- Removing legacy source files; first preserve them, then remove them in a
  separate cleanup after the canonical demo path is proven.
