#!/usr/bin/env bash
# Start the current AquaPredict demo stack locally, or deploy it over SSH.
# Local:  ./deploy_now.sh
# Remote: ./deploy_now.sh user@demo-host [remote-directory]

set -Eeuo pipefail

usage() {
  echo "Usage: $0 [user@host [remote-directory]]" >&2
  echo "" >&2
  echo "Without a host, starts the demo locally at http://localhost." >&2
  echo "Required: .env.demo, credentials/gee_key.json, and Docker Compose." >&2
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

target=${1:-}
remote_dir=${2:-aquapredict-demo}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
env_file="$script_dir/.env.demo"
credentials_dir="$script_dir/credentials"

if [[ ! -f "$env_file" ]]; then
  echo "Missing $env_file. Copy .env.demo.example and configure it first." >&2
  exit 1
fi

if [[ ! -f "$credentials_dir/gee_key.json" ]]; then
  echo "Missing $credentials_dir/gee_key.json. GEE is required for this demo deployment." >&2
  exit 1
fi

if [[ -z "$target" ]]; then
  command -v docker >/dev/null || {
    echo "Missing required command: docker" >&2
    exit 1
  }
  docker compose version >/dev/null

  echo "Building and starting the local demo stack..."
  cd "$script_dir"
  chmod 700 credentials
  chmod 600 credentials/gee_key.json .env.demo
  docker compose --env-file .env.demo -f docker-compose.demo.yml up -d --build

  echo "Waiting for the service health check..."
  backend_id=$(docker compose --env-file .env.demo -f docker-compose.demo.yml ps -q backend)
  if [[ -z "$backend_id" ]]; then
    echo "Backend container was not created." >&2
    exit 1
  fi
  for attempt in $(seq 1 30); do
    if [[ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$backend_id")" == "healthy" ]]; then
      break
    fi
    if [[ "$attempt" == 30 ]]; then
      docker compose --env-file .env.demo -f docker-compose.demo.yml ps
      docker compose --env-file .env.demo -f docker-compose.demo.yml logs --tail=100 backend
      exit 1
    fi
    sleep 2
  done

  demo_port=$(awk -F= '$1 == "DEMO_PORT" { port=$2 } END { print port }' .env.demo)
  demo_port=${demo_port:-80}
  curl --fail --silent --show-error "http://localhost:${demo_port}/health" >/dev/null
  docker compose --env-file .env.demo -f docker-compose.demo.yml ps
  echo
  echo "Local demo ready: http://localhost:${demo_port}"
  exit 0
fi

# Keep the target safely within the remote account's home directory.
if [[ ! "$remote_dir" =~ ^[A-Za-z0-9._/-]+$ || "$remote_dir" == *..* || "$remote_dir" == /* ]]; then
  echo "Remote directory must be a safe relative path (for example: aquapredict-demo)." >&2
  exit 2
fi

for command in rsync ssh; do
  command -v "$command" >/dev/null || {
    echo "Missing required command: $command" >&2
    exit 1
  }
done

echo "Checking Docker Compose on $target..."
ssh "$target" 'docker compose version >/dev/null'

echo "Syncing the demo application to $target:$remote_dir..."
# Credentials and .env files are deliberately transferred in dedicated commands below.
rsync -az \
  --exclude '.git/' \
  --exclude '.env*' \
  --exclude 'credentials/' \
  --exclude '**/__pycache__/' \
  --exclude '**/.pytest_cache/' \
  --exclude 'modules/frontend/node_modules/' \
  --exclude 'modules/frontend/.next/' \
  "$script_dir/" "$target:$remote_dir/"

echo "Syncing deployment configuration and GEE credential..."
ssh "$target" "mkdir -p -- '$remote_dir/credentials'"
rsync -az "$env_file" "$target:$remote_dir/.env.demo"
rsync -az "$credentials_dir/gee_key.json" "$target:$remote_dir/credentials/gee_key.json"

echo "Building and starting the demo stack..."
ssh "$target" "REMOTE_DIR='$remote_dir' bash -s" <<'REMOTE'
set -Eeuo pipefail

cd "$REMOTE_DIR"
chmod 700 credentials
chmod 600 credentials/gee_key.json .env.demo
docker compose --env-file .env.demo -f docker-compose.demo.yml up -d --build

echo "Waiting for the service health check..."
backend_id=$(docker compose --env-file .env.demo -f docker-compose.demo.yml ps -q backend)
if [[ -z "$backend_id" ]]; then
  echo "Backend container was not created." >&2
  exit 1
fi
for attempt in $(seq 1 30); do
  if [[ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$backend_id")" == "healthy" ]]; then
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    docker compose --env-file .env.demo -f docker-compose.demo.yml ps
    docker compose --env-file .env.demo -f docker-compose.demo.yml logs --tail=100 backend
    exit 1
  fi
  sleep 2
done

demo_port=$(awk -F= '$1 == "DEMO_PORT" { port=$2 } END { print port }' .env.demo)
demo_port=${demo_port:-80}
curl --fail --silent --show-error "http://localhost:${demo_port}/health" >/dev/null
docker compose --env-file .env.demo -f docker-compose.demo.yml ps
REMOTE

echo
echo "Deployment complete. Open: http://$target"
echo "For HTTPS or a custom domain, place a TLS-terminating proxy in front of port 80."
