"""Provision AquaPredict's Databricks Bronze, Silver, Gold, Ops and Genie layer."""

import asyncio
import json

from app.services.databricks_service import databricks_service


async def main() -> None:
    print(json.dumps(await databricks_service.bootstrap_decision_layer(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
