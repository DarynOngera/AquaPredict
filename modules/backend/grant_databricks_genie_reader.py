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
    access_token = await databricks_service._access_token()
    await asyncio.to_thread(apply_grants, statements, access_token)
    print(f"Granted read-only Genie access to {email}")


def apply_grants(statements: list[str], access_token: str) -> None:
    """Use the synchronous SQL connector so each GRANT has committed."""
    from databricks import sql

    hostname = databricks_service.host.removeprefix("https://").removeprefix("http://")
    http_path = databricks_service.http_path or f"/sql/1.0/warehouses/{databricks_service.warehouse_id}"
    with sql.connect(server_hostname=hostname, http_path=http_path, access_token=access_token) as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(main(args.email))
