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

import httpx


logger = logging.getLogger(__name__)
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabricksService:
    def __init__(self) -> None:
        self.host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
        self.warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
        self.catalog = os.getenv("DATABRICKS_CATALOG", "aquapredict")
        self.schema = os.getenv("DATABRICKS_SCHEMA", "reporting")
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
            columns = ", ".join(values.keys())
            literals = ", ".join(self._literal(value) for value in values.values())
            await self._execute(f"INSERT INTO {self._table(table)} ({columns}) VALUES ({literals})")
        except Exception as exc:  # Mirroring must never make product requests fail.
            logger.warning("Databricks mirror failed for %s: %s", table, exc)

    async def _ensure_tables(self) -> None:
        if self._initialized:
            return
        async with self._initialization_lock:
            if self._initialized:
                return
            await self._execute(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{self.schema}")
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
            self._initialized = True

    async def _execute(self, statement: str) -> None:
        headers = {"Authorization": f"Bearer {await self._access_token()}"}
        payload = {"warehouse_id": self.warehouse_id, "statement": statement, "wait_timeout": "10s"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.host}/api/2.0/sql/statements", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        state = result.get("status", {}).get("state")
        if state == "FAILED":
            raise RuntimeError(result.get("status", {}).get("error", {}).get("message", "Databricks SQL execution failed"))

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
        return f"{self.catalog}.{self.schema}.{table}"

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
