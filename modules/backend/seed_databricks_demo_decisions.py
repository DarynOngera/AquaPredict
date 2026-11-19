"""Seed deterministic, clearly labelled scenarios for the AquaPredict Genie demo."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

from databricks import sql

from app.services.databricks_service import databricks_service


LOCATIONS = [
    ("Turkana scenario north", "Turkana", 3.119, 35.597, 0.88),
    ("Merti scenario", "Isiolo", 1.854, 38.120, 0.81),
    ("Eastlands scenario", "Nairobi", -1.286, 36.870, 0.72),
    ("Loitokitok scenario", "Kajiado", -2.925, 37.500, 0.67),
    ("Athi scenario", "Machakos", -1.500, 37.270, 0.61),
    ("Suswa scenario", "Narok", -1.170, 36.350, 0.48),
    ("Tana scenario", "Garissa", -0.450, 39.650, 0.44),
    ("Mwingi scenario", "Kitui", -0.940, 38.060, 0.39),
    ("Nyando scenario", "Kisumu", -0.180, 34.750, 0.76),
    ("Likoni scenario", "Mombasa", -4.080, 39.660, 0.31),
]


def statement_for_seed() -> str:
    target = databricks_service._qualified("bronze", "aquapredict_events")
    now = datetime.now(timezone.utc)
    rows = []
    for index, (location_name, county, latitude, longitude, base_probability) in enumerate(LOCATIONS):
        for observation in range(3):
            probability = round(max(0.05, min(0.95, base_probability + (observation - 1) * 0.025)), 3)
            event_at = (now - timedelta(days=(len(LOCATIONS) - index) * 3 + observation)).isoformat()
            payload = json.dumps({
                "location_name": location_name,
                "county": county,
                "is_synthetic": True,
                "scenario": "AquaPredict talk demo",
                "scenario_note": "Synthetic decision-support scenario; not a field observation.",
            })
            values = {
                "record_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"aquapredict-demo-{location_name}-{observation}")),
                "event_type": "prediction",
                "event_at": event_at,
                "latitude": latitude,
                "longitude": longitude,
                # Low-confidence present cases deliberately exercise the
                # Gold "collect_more_evidence" decision branch for the demo.
                "result": "present" if probability >= 0.35 else "absent",
                "probability": probability,
                "data_source": "synthetic_demo",
                "report_type": None,
                "payload_json": payload,
                "ingested_at": now.isoformat(),
            }
            rows.append("(" + ", ".join(databricks_service._literal(value) for value in values.values()) + ")")
    columns = "record_id, event_type, event_at, latitude, longitude, result, probability, data_source, report_type, payload_json, ingested_at"
    return f"INSERT INTO {target} ({columns}) VALUES " + ", ".join(rows)


async def main() -> None:
    await databricks_service.bootstrap_decision_layer()
    token = await databricks_service._access_token()
    hostname = databricks_service.host.removeprefix("https://").removeprefix("http://")
    http_path = databricks_service.http_path or f"/sql/1.0/warehouses/{databricks_service.warehouse_id}"
    target = databricks_service._qualified("bronze", "aquapredict_events")

    def seed() -> None:
        with sql.connect(server_hostname=hostname, http_path=http_path, access_token=token) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {target} WHERE data_source = 'synthetic_demo'")
                cursor.execute(statement_for_seed())

    await asyncio.to_thread(seed)
    print(f"Seeded {len(LOCATIONS) * 3} synthetic demo prediction scenarios into {target}")


if __name__ == "__main__":
    asyncio.run(main())
