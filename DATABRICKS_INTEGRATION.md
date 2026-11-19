# Databricks report mirror

AquaPredict can optionally mirror completed aquifer predictions, recharge
forecasts, and generated PDF report metadata to a Databricks SQL Warehouse.
It is **disabled by default**. The existing local and demo flows retain their
current behaviour if Databricks is not configured or if it is temporarily
unavailable.

## Decision layer and Genie

The bootstrap command creates a governed decision layer without changing the
existing `reporting` tables:

| Schema | Purpose |
| --- | --- |
| `reporting` | Backward-compatible operational output tables. |
| `bronze` | Immutable raw API event envelopes, including the original JSON payload. |
| `silver` | Standardised event contract with cleaned labels and valid prediction types. |
| `gold` | Decision-ready aquifer recommendations and daily KPIs. |
| `ops` | Live quality checks for all three decision layers. |

Gold views are the only business-facing sources in the bundled Genie Agent.
The agent is instructed to check `ops.decision_layer_quality` before making
trust statements and never to use Bronze payloads for recommendations.
Live AquaPredict events currently enter Bronze as immutable raw JSON envelopes;
future CSV and external API feeds can use a Unity Catalog volume and feed the
same Silver contract without changing Gold, Genie, or the application consumer.

To provision or update the layer locally, enable Genie and run the bootstrap
inside the backend container:

```dotenv
DATABRICKS_GENIE_ENABLED=true
DATABRICKS_GENIE_TITLE=AquaPredict Decision Intelligence
```

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml exec backend \
  python bootstrap_databricks_decision_layer.py
```

The command is idempotent: schemas, tables, and views are recreated safely;
an existing Genie Agent with the configured title is reused. The service
principal's OAuth secret needs the `genie` API scope in addition to SQL access.

After provisioning, use these starter Genie questions:

- Which locations should be prioritized for field validation?
- What is the average aquifer probability by decision date?
- Are all Bronze, Silver, and Gold data quality checks passing?

For a repeatable talk demo, run `seed_databricks_demo_decisions.py` in the
backend container. It seeds 30 named, dated `synthetic_demo` predictions across
ten Kenyan counties. Gold exposes the location name, county, and synthetic flag
so Genie can answer useful questions while clearly distinguishing scenarios
from live observations.

Genie evaluates Unity Catalog access as the person asking the question. Grant
each demo user only the Gold and Ops assets, never Bronze:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml exec backend \
  python grant_databricks_genie_reader.py user@example.com
```

## Configure the demo

Copy the example configuration and add the following to `.env.demo`:

```dotenv
DATABRICKS_ENABLED=true
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_WAREHOUSE_ID=your-sql-warehouse-id
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-sql-warehouse-id
DATABRICKS_CATALOG=aquapredict
DATABRICKS_SCHEMA=reporting
DATABRICKS_CLIENT_ID=your-service-principal-application-id
DATABRICKS_CLIENT_SECRET=your-oauth-secret
```

OAuth machine-to-machine credentials are the recommended authentication
method. `DATABRICKS_TOKEN` remains available as a legacy personal-access-token
alternative, but should not be used alongside OAuth credentials.

For maximum warehouse compatibility, copy the **HTTP Path** exactly from the
warehouse's **Connection Details** tab into `DATABRICKS_HTTP_PATH`. It is not a
secret and can differ from the path inferred from a warehouse ID.

The integration creates the schema and three Delta tables on first use:

- `aquapredict.reporting.predictions`
- `aquapredict.reporting.recharge_forecasts`
- `aquapredict.reporting.reports`

Each row includes query-friendly columns such as time, location, outcome and
source, plus `payload_json` for the full immutable API/export payload.

## Required Databricks access

Grant the service principal `CAN USE` on the SQL Warehouse, and Unity Catalog
permissions to use the chosen catalog and schema and to create/modify tables
there. If catalog or schema creation is centrally managed, create them ahead
of time and grant `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`, and `MODIFY`.

The non-sensitive status endpoint is available at
`GET /api/v1/integrations/databricks`; it only reports whether the integration
is enabled and configured, never credentials.

The backend first uses Databricks SQL Statement Execution v1 and automatically
falls back to the warehouse-scoped v2 endpoint required by newer Lakehouse
Runtime warehouses. For conventional SQL Warehouses in workspaces that do not
offer either REST endpoint, it uses the Databricks SQL connector at the
warehouse's standard HTTP path. It authenticates to the workspace with the
service principal and sends no credentials in report payloads.
