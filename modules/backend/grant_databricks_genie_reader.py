"""Grant one Databricks user read-only access to AquaPredict Genie assets."""

import argparse
import asyncio

from app.services.databricks_service import databricks_service


def principal(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


async def main(email: str) -> None:
    if not databricks_service.configured:
        raise RuntimeError("Databricks mirroring is not configured")

    user = principal(email)
    catalog = databricks_service.catalog
    statements = [
        f"GRANT USE CATALOG ON CATALOG {catalog} TO {user}",
        f"GRANT USE SCHEMA ON SCHEMA {catalog}.gold TO {user}",
        f"GRANT USE SCHEMA ON SCHEMA {catalog}.ops TO {user}",
        f"GRANT SELECT ON VIEW {catalog}.gold.aquifer_decisions TO {user}",
        f"GRANT SELECT ON VIEW {catalog}.gold.decision_kpis TO {user}",
        f"GRANT SELECT ON VIEW {catalog}.ops.decision_layer_quality TO {user}",
    ]
    for statement in statements:
        await databricks_service._execute(statement)
    print(f"Granted read-only Genie access to {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(main(args.email))
