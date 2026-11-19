"""Optional Databricks SQL Warehouse persistence for AquaPredict outputs.

The adapter is deliberately fail-open: the demo remains fully functional when
Databricks is not configured or temporarily unavailable.
"""

import asyncio
import json
import logging
import math
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx


logger = logging.getLogger(__name__)
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabricksService:
    def __init__(self) -> None:
        self.host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
        self.http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        self.catalog = os.getenv("DATABRICKS_CATALOG", "aquapredict")
        self.schema = os.getenv("DATABRICKS_SCHEMA", "reporting")
        self.genie_enabled = os.getenv("DATABRICKS_GENIE_ENABLED", "false").lower() == "true"
        self.genie_title = os.getenv("DATABRICKS_GENIE_TITLE", "AquaPredict Decision Intelligence")
        self.genie_parent_path = os.getenv("DATABRICKS_GENIE_PARENT_PATH", "")
        self.genie_readers = [email.strip() for email in os.getenv("DATABRICKS_GENIE_READERS", "").split(",") if email.strip()]
        self.enabled = os.getenv("DATABRICKS_ENABLED", "false").lower() == "true"
        self.client_id = os.getenv("DATABRICKS_CLIENT_ID", "")
        self.client_secret = os.getenv("DATABRICKS_CLIENT_SECRET", "")
        self.pat = os.getenv("DATABRICKS_TOKEN", "")
        self._token: Optional[str] = None
        self._token_expires_at = 0.0
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        has_auth = bool(self.pat or (self.client_id and self.client_secret))
        valid_namespace = bool(IDENTIFIER.match(self.catalog) and IDENTIFIER.match(self.schema))
        return self.enabled and bool(self.host) and bool(self.warehouse_id) and has_auth and valid_namespace

    def status(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "configured": False, "message": "Databricks mirroring is disabled"}
        return {
            "enabled": True,
            "configured": self.configured,
            "host": self.host,
            "catalog": self.catalog,
            "schema": self.schema,
            "auth": "oauth_m2m" if self.client_id and self.client_secret else "personal_access_token" if self.pat else "missing",
            "decision_layer": {"schemas": ["bronze", "silver", "gold", "ops"]},
            "genie": {"enabled": self.genie_enabled, "title": self.genie_title},
        }

    async def record_prediction(self, prediction: Dict[str, Any]) -> None:
        location = prediction.get("location", {})
        await self._record(
            "predictions",
            {
                "record_id": str(uuid.uuid4()),
                "created_at": prediction.get("timestamp") or self._now(),
                "latitude": location.get("lat"),
                "longitude": location.get("lon"),
                "result": prediction.get("prediction"),
                "probability": prediction.get("probability"),
                "data_source": prediction.get("data_source"),
                "payload_json": json.dumps(prediction, default=str),
            },
        )

    async def record_forecast(self, forecast: Dict[str, Any]) -> None:
        location = forecast.get("location", {})
        await self._record(
            "recharge_forecasts",
            {
                "record_id": str(uuid.uuid4()),
                "created_at": forecast.get("timestamp") or self._now(),
                "latitude": location.get("lat"),
                "longitude": location.get("lon"),
                "data_source": forecast.get("data_source"),
                "payload_json": json.dumps(forecast, default=str),
            },
        )

    async def record_report(self, report: Dict[str, Any]) -> None:
        prediction = report.get("prediction") or {}
        location = prediction.get("location", {})
        await self._record(
            "reports",
            {
                "record_id": str(uuid.uuid4()),
                "created_at": self._now(),
                "latitude": location.get("lat"),
                "longitude": location.get("lon"),
                "report_type": "analysis_report",
                "payload_json": json.dumps(report, default=str),
            },
        )

    async def _record(self, table: str, values: Dict[str, Any]) -> None:
        if not self.configured:
            return
        try:
            await self._ensure_tables()
            await self._insert(self._table(table), values)
            await self._insert(
                self._qualified("bronze", "aquapredict_events"),
                {
                    "record_id": values["record_id"],
                    "event_type": table.removesuffix("s"),
                    "event_at": values["created_at"],
                    "latitude": values.get("latitude"),
                    "longitude": values.get("longitude"),
                    "result": values.get("result"),
                    "probability": values.get("probability"),
                    "data_source": values.get("data_source"),
                    "report_type": values.get("report_type"),
                    "payload_json": values["payload_json"],
                    "ingested_at": self._now(),
                },
            )
        except Exception as exc:  # Mirroring must never make product requests fail.
            logger.warning("Databricks mirror failed for %s: %s", table, exc)

    async def _ensure_tables(self) -> None:
        if self._initialized:
            return
        async with self._initialization_lock:
            if self._initialized:
                return
            for schema in (self.schema, "bronze", "silver", "gold", "ops"):
                await self._execute(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema}")
            await self._execute(
                f"CREATE TABLE IF NOT EXISTS {self._table('predictions')} "
                "(record_id STRING, created_at TIMESTAMP, latitude DOUBLE, longitude DOUBLE, result STRING, "
                "probability DOUBLE, data_source STRING, payload_json STRING) USING DELTA"
            )
            await self._execute(
                f"CREATE TABLE IF NOT EXISTS {self._table('recharge_forecasts')} "
                "(record_id STRING, created_at TIMESTAMP, latitude DOUBLE, longitude DOUBLE, data_source STRING, "
                "payload_json STRING) USING DELTA"
            )
            await self._execute(
                f"CREATE TABLE IF NOT EXISTS {self._table('reports')} "
                "(record_id STRING, created_at TIMESTAMP, latitude DOUBLE, longitude DOUBLE, report_type STRING, "
                "payload_json STRING) USING DELTA"
            )
            await self._execute(
                f"CREATE TABLE IF NOT EXISTS {self._qualified('bronze', 'aquapredict_events')} "
                "(record_id STRING, event_type STRING, event_at TIMESTAMP, latitude DOUBLE, longitude DOUBLE, "
                "result STRING, probability DOUBLE, data_source STRING, report_type STRING, payload_json STRING, "
                "ingested_at TIMESTAMP) USING DELTA"
            )
            await self._create_decision_views()
            for reader in self.genie_readers:
                await self.grant_genie_reader(reader)
            self._initialized = True

    async def _create_decision_views(self) -> None:
        """Create governed Silver, Gold and Ops contracts over immutable Bronze events."""
        bronze = self._qualified("bronze", "aquapredict_events")
        await self._execute(
            f"CREATE OR REPLACE VIEW {self._qualified('silver', 'aquapredict_events')} AS "
            "SELECT record_id, lower(trim(event_type)) AS event_type, event_at, latitude, longitude, "
            "lower(trim(result)) AS result, cast(probability AS DOUBLE) AS probability, "
            "lower(trim(data_source)) AS data_source, report_type, "
            "coalesce(get_json_object(payload_json, '$.location_name'), concat('Unnamed location ', cast(latitude AS STRING), ', ', cast(longitude AS STRING))) AS location_name, "
            "coalesce(get_json_object(payload_json, '$.county'), 'Unspecified') AS county, "
            "coalesce(cast(get_json_object(payload_json, '$.is_synthetic') AS BOOLEAN), false) AS is_synthetic, "
            "payload_json, ingested_at "
            f"FROM {bronze} WHERE record_id IS NOT NULL AND event_type IN ('prediction', 'recharge_forecast', 'report')"
        )
        silver = self._qualified("silver", "aquapredict_events")
        await self._execute(
            f"CREATE OR REPLACE VIEW {self._qualified('gold', 'aquifer_decisions')} AS "
            "SELECT record_id, event_at AS decision_at, location_name, county, latitude, longitude, result, probability, "
            "CASE WHEN result = 'present' AND probability >= 0.75 THEN 'prioritize_field_validation' "
            "WHEN result = 'present' AND probability >= 0.50 THEN 'review_with_context' "
            "WHEN result = 'present' THEN 'collect_more_evidence' "
            "ELSE 'do_not_prioritize' END AS recommended_action, "
            "CASE WHEN probability >= 0.75 THEN 'high' WHEN probability >= 0.50 THEN 'medium' ELSE 'low' END AS confidence_band "
            f"FROM {silver} WHERE event_type = 'prediction'"
        )
        await self._execute(
            f"CREATE OR REPLACE VIEW {self._qualified('gold', 'decision_kpis')} AS "
            "SELECT cast(decision_at AS DATE) AS decision_date, county, count(*) AS predictions, "
            "round(avg(probability), 4) AS average_probability, "
            "sum(CASE WHEN recommended_action = 'prioritize_field_validation' THEN 1 ELSE 0 END) AS high_priority_locations "
            f"FROM {self._qualified('gold', 'aquifer_decisions')} GROUP BY cast(decision_at AS DATE), county"
        )
        await self._execute(
            f"CREATE OR REPLACE VIEW {self._qualified('ops', 'decision_layer_quality')} AS "
            "SELECT 'bronze' AS layer, 'payload_present' AS check_name, "
            "count(CASE WHEN payload_json IS NULL OR length(payload_json) = 0 THEN 1 END) = 0 AS passed, "
            "count(CASE WHEN payload_json IS NULL OR length(payload_json) = 0 THEN 1 END) AS failed_rows, current_timestamp() AS checked_at "
            f"FROM {bronze} UNION ALL "
            "SELECT 'silver', 'prediction_probability_in_range', "
            "count(CASE WHEN event_type = 'prediction' AND (probability IS NULL OR probability < 0 OR probability > 1) THEN 1 END) = 0, "
            "count(CASE WHEN event_type = 'prediction' AND (probability IS NULL OR probability < 0 OR probability > 1) THEN 1 END), current_timestamp() "
            f"FROM {silver} UNION ALL "
            "SELECT 'gold', 'decision_action_present', count(CASE WHEN recommended_action IS NULL THEN 1 END) = 0, "
            "count(CASE WHEN recommended_action IS NULL THEN 1 END), current_timestamp() "
            f"FROM {self._qualified('gold', 'aquifer_decisions')}"
        )

    async def bootstrap_decision_layer(self) -> Dict[str, Any]:
        """Provision the medallion contracts and optionally a reusable Genie Agent."""
        if not self.configured:
            return {"configured": False, "message": "Databricks mirroring is not configured"}
        await self._ensure_tables()
        genie = await self._ensure_genie_space() if self.genie_enabled else {"enabled": False}
        return {
            "configured": True,
            "catalog": self.catalog,
            "schemas": [self.schema, "bronze", "silver", "gold", "ops"],
            "genie": genie,
        }

    async def _ensure_genie_space(self) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {await self._access_token()}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.host}/api/2.0/genie/spaces", headers=headers)
            response.raise_for_status()
            for space in response.json().get("spaces", []):
                if space.get("title") == self.genie_title:
                    update = await client.patch(
                        f"{self.host}/api/2.0/genie/spaces/{space['space_id']}",
                        headers=headers,
                        json={
                            "description": "Governed AquaPredict demo decisions, KPIs, and data quality checks.",
                            "serialized_space": json.dumps(self._genie_space_config()),
                        },
                    )
                    update.raise_for_status()
                    return {"enabled": True, "created": False, "updated": True, "space_id": space.get("space_id"), "title": self.genie_title}
            config = self._genie_space_config()
            payload: Dict[str, Any] = {
                "warehouse_id": self.warehouse_id,
                "title": self.genie_title,
                "description": "Governed AquaPredict aquifer decisions, KPIs, and data quality checks.",
                "serialized_space": json.dumps(config),
            }
            if self.genie_parent_path:
                payload["parent_path"] = self.genie_parent_path
            response = await client.post(f"{self.host}/api/2.0/genie/spaces", headers=headers, json=payload)
            if response.is_error:
                raise RuntimeError(
                    f"Genie space creation returned {response.status_code}: {response.text[:2000]}"
                )
            space = response.json()
        return {"enabled": True, "created": True, "space_id": space.get("space_id"), "title": self.genie_title}

    def _genie_space_config(self) -> Dict[str, Any]:
        gold_decisions = self._qualified("gold", "aquifer_decisions")
        gold_kpis = self._qualified("gold", "decision_kpis")
        quality = self._qualified("ops", "decision_layer_quality")
        return {
            "version": 2,
            "config": {"sample_questions": [
                {"id": "00000000000000000000000000000001", "question": ["Which locations should be prioritized for field validation?"]},
                {"id": "00000000000000000000000000000002", "question": ["Which counties have the most high-priority field-validation locations?"]},
                {"id": "00000000000000000000000000000003", "question": ["Are all Bronze, Silver, and Gold data quality checks passing?"]},
            ]},
            "data_sources": {"tables": [
                {"identifier": gold_decisions, "description": ["One row per aquifer prediction with named location, county, governed recommended action, and confidence band."]},
                {"identifier": gold_kpis, "description": ["Daily and county-level decision KPIs derived only from Gold aquifer decisions."]},
                {"identifier": quality, "description": ["Automated data quality status for the Bronze, Silver, and Gold decision layers."]},
            ]},
            "instructions": {"text_instructions": [
                {"id": "00000000000000000000000000000011", "content": [
                    "Use Gold views for business decisions. Never use Bronze raw payloads for recommendations.",
                    "A high-priority location means recommended_action is prioritize_field_validation. Treat predictions as decision support, not a drilling guarantee.",
                    "When asked about data trust, first query ops.decision_layer_quality and report any failing checks."
                ]},
            ]},
        }

    async def _insert(self, target: str, values: Dict[str, Any]) -> None:
        columns = ", ".join(values.keys())
        literals = ", ".join(self._literal(value) for value in values.values())
        await self._execute(f"INSERT INTO {target} ({columns}) VALUES ({literals})")

    async def grant_genie_reader(self, email: str) -> None:
        """Grant a named user only the Gold and Ops views consumed by Genie."""
        if not self.configured:
            raise RuntimeError("Databricks mirroring is not configured")
        principal = "`" + email.replace("`", "``") + "`"
        statements = [
            f"GRANT USE CATALOG ON CATALOG {self.catalog} TO {principal}",
            f"GRANT USE SCHEMA ON SCHEMA {self.catalog}.gold TO {principal}",
            f"GRANT USE SCHEMA ON SCHEMA {self.catalog}.ops TO {principal}",
            f"GRANT SELECT ON VIEW {self.catalog}.gold.aquifer_decisions TO {principal}",
            f"GRANT SELECT ON VIEW {self.catalog}.gold.decision_kpis TO {principal}",
            f"GRANT SELECT ON VIEW {self.catalog}.ops.decision_layer_quality TO {principal}",
        ]
        access_token = await self._access_token()
        await asyncio.to_thread(self._apply_grants_via_sql_connector, statements, access_token)

    def _apply_grants_via_sql_connector(self, statements: list[str], access_token: str) -> None:
        from databricks import sql

        hostname = self.host.removeprefix("https://").removeprefix("http://")
        http_path = self.http_path or f"/sql/1.0/warehouses/{self.warehouse_id}"
        with sql.connect(server_hostname=hostname, http_path=http_path, access_token=access_token) as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

    async def _execute(self, statement: str) -> None:
        access_token = await self._access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {"warehouse_id": self.warehouse_id, "statement": statement, "wait_timeout": "10s"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.host}/api/2.0/sql/statements/", headers=headers, json=payload)
            # Lakehouse Runtime warehouses expose Statement Execution v2.
            # Keep the v1 endpoint first for all conventional warehouse types,
            # then fall back only when the workspace reports that it is absent.
            if response.status_code == 404:
                # The Lakehouse Runtime route currently JSON-decodes path
                # parameters. Encode an all-numeric warehouse ID as a JSON
                # string so it is not interpreted as an integer.
                warehouse_path_id = self.warehouse_id
                if warehouse_path_id.isdigit():
                    warehouse_path_id = quote(json.dumps(warehouse_path_id), safe="")
                response = await client.post(
                    f"{self.host}/api/2.0/sql/warehouses/{warehouse_path_id}/statements",
                    headers=headers,
                    json={
                        "statement": statement,
                        "catalog": self.catalog,
                        "schema": self.schema,
                        "format": "JSON_ARRAY",
                        "wait_timeout": "10s",
                    },
                )
            connector_fallback = (
                response.status_code == 404
                or (
                    response.status_code == 400
                    and "warehouse type is not supported by this api" in response.text.lower()
                )
            )
            if connector_fallback:
                await asyncio.to_thread(self._execute_via_sql_connector, statement, access_token)
                return
            if response.is_error:
                # Databricks returns the actionable warehouse/API validation
                # reason in its JSON body. Keep it bounded for safe logs.
                detail = response.text[:1000]
                raise RuntimeError(
                    f"Databricks SQL request returned {response.status_code}: {detail}"
                )
            result = response.json()
        state = result.get("status", {}).get("state")
        if state == "FAILED":
            raise RuntimeError(result.get("status", {}).get("error", {}).get("message", "Databricks SQL execution failed"))

    def _execute_via_sql_connector(self, statement: str, access_token: str) -> None:
        """Execute against the standard SQL Warehouse Thrift endpoint.

        This is the compatibility route for workspaces that do not expose the
        Statement Execution API for conventional SQL warehouse types.
        """
        from databricks import sql

        hostname = self.host.removeprefix("https://").removeprefix("http://")
        with sql.connect(
            server_hostname=hostname,
            http_path=self.http_path or f"/sql/1.0/warehouses/{self.warehouse_id}",
            access_token=access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement)

    async def _access_token(self) -> str:
        if self.pat:
            return self.pat
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.host}/oidc/v1/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials", "scope": "all-apis"},
            )
            response.raise_for_status()
            token = response.json()
        self._token = token["access_token"]
        self._token_expires_at = time.time() + int(token.get("expires_in", 3600))
        return self._token

    def _table(self, table: str) -> str:
        return self._qualified(self.schema, table)

    def _qualified(self, schema: str, table: str) -> str:
        return f"{self.catalog}.{schema}.{table}"

    @staticmethod
    def _literal(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                return "NULL"
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


databricks_service = DatabricksService()
