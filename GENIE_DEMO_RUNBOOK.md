# AquaPredict Genie Decision Demo

This runbook presents AquaPredict as a governed AI and data science decision
system. The Genie Agent only reads Gold decision views and the Ops quality
checks. It never uses the raw Bronze payloads to make a recommendation.

## Before the talk

Seed the talk scenarios, then optionally run one live AquaPredict prediction.
The seed replaces only the prior `synthetic_demo` rows and leaves live app data
intact:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml exec backend \
  python seed_databricks_demo_decisions.py
```

The seed creates 30 clearly labelled synthetic decision scenarios across ten
Kenyan counties. They are useful for a repeatable demo, not field observations.

In Databricks, open **Genie Agents** and select **AquaPredict Decision
Intelligence**. Use the SQL warehouse configured for the agent.

## Demonstrate the lineage

Start in Catalog Explorer and show these schemas in the `workspace` catalog:

1. `bronze.aquapredict_events` keeps the immutable event envelope and raw JSON.
2. `silver.aquapredict_events` standardises event type, source, prediction
   outcome, and probability.
3. `gold.aquifer_decisions` turns a prediction into a governed recommended
   action and confidence band.
4. `gold.decision_kpis` provides day-level decision metrics.
5. `ops.decision_layer_quality` proves each layer's current quality checks.

## Ask Genie

Use these questions in order:

1. **Are all Bronze, Silver, and Gold data quality checks passing?**
2. **Which locations should be prioritized for field validation?**
3. **Which counties have the most high-priority field-validation locations in the synthetic demo scenario?**
4. **Which scenario locations should collect more evidence before field validation?**

The expected decision rule is visible in `gold.aquifer_decisions`:

- `prioritize_field_validation`: aquifer present with probability at least 0.75.
- `review_with_context`: aquifer present with probability from 0.50 to 0.7499.
- `collect_more_evidence`: aquifer present below 0.50.
- `do_not_prioritize`: no aquifer predicted.

Predictions are decision support, not a guarantee that drilling will succeed.

## SQL proof points

```sql
SELECT *
FROM workspace.ops.decision_layer_quality
ORDER BY layer, check_name;
```

```sql
SELECT decision_at, location_name, county, latitude, longitude, probability, confidence_band, recommended_action, data_source, is_synthetic
FROM workspace.gold.aquifer_decisions
ORDER BY decision_at DESC;
```

```sql
SELECT *
FROM workspace.gold.decision_kpis
ORDER BY decision_date DESC;
```

## If new events are absent

Run a prediction in AquaPredict and wait briefly for the background mirror.
Then inspect the backend without exposing any credentials:

```bash
docker compose --env-file .env.demo -f docker-compose.demo.yml logs --tail=100 backend
```
