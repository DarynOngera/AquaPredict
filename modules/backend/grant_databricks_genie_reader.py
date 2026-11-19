"""Grant one Databricks user read-only access to AquaPredict Genie assets."""

import argparse
import asyncio

from app.services.databricks_service import databricks_service


async def main(email: str) -> None:
    if not databricks_service.configured:
        raise RuntimeError("Databricks mirroring is not configured")

    await databricks_service.grant_genie_reader(email)
    print(f"Granted read-only Genie access to {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(main(args.email))
