# Databricks report mirror

AquaPredict can optionally mirror completed aquifer predictions, recharge
forecasts, and generated PDF report metadata to a Databricks SQL Warehouse.
It is **disabled by default**. The existing local and demo flows retain their
current behaviour if Databricks is not configured or if it is temporarily
unavailable.

## Configure the demo

Copy the example configuration and add the following to `.env.demo`:

```dotenv
DATABRICKS_ENABLED=true
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_WAREHOUSE_ID=your-sql-warehouse-id
DATABRICKS_CATALOG=aquapredict
DATABRICKS_SCHEMA=reporting
DATABRICKS_CLIENT_ID=your-service-principal-application-id
DATABRICKS_CLIENT_SECRET=your-oauth-secret
```

OAuth machine-to-machine credentials are the recommended authentication
method. `DATABRICKS_TOKEN` remains available as a legacy personal-access-token
alternative, but should not be used alongside OAuth credentials.

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
