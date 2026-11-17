#!/usr/bin/env bash

set -euo pipefail

base_url="${1:-http://localhost}"

curl --fail --silent --show-error "${base_url}/" >/dev/null
curl --fail --silent --show-error "${base_url}/api/health" >/dev/null
curl --fail --silent --show-error \
  --request POST "${base_url}/api/inference/predict" \
  --header 'Content-Type: application/json' \
  --data '{"lon":36.8219,"lat":-1.2921,"date":"2026-11-17","model_name":"random_forest"}' \
  >/dev/null

echo "Demo smoke checks passed: ${base_url}"
