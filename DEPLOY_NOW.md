# Deploy the demo

`deploy_now.sh` deploys the current Docker demo stack: the Next.js frontend,
FastAPI backend, Nginx proxy, model artifacts, and the configured Google Earth
Engine credential. It replaces the retired static `simple_api.py` deployment.

## Local demo

Create `.env.demo` from the example and set the real values:

```bash
cp .env.demo.example .env.demo
```

Place the GEE service-account JSON key at `credentials/gee_key.json`. Both are
ignored by Git. For local use set `CORS_ORIGINS=http://localhost` and leave
`DEMO_PORT=80` unless that port is already occupied.

With Docker Engine and the Docker Compose plugin running, start the demo:

```bash
./deploy_now.sh
```

It builds the stack, waits for the backend health check, and opens at
`http://localhost` (or `http://localhost:DEMO_PORT` if you changed the port).
The backend and frontend ports remain internal to the Docker network.

## Optional remote deployment

Use a Linux host with Docker Engine and the Docker Compose plugin installed.
The SSH account must be allowed to run `docker compose` without `sudo`, and the
host firewall/security group must allow inbound TCP port 80 (or `DEMO_PORT`).

```bash
./deploy_now.sh opc@YOUR_SERVER_IP
```

An optional second argument selects a safe relative directory under that
user's home directory:

```bash
./deploy_now.sh opc@YOUR_SERVER_IP aquapredict-demo
```

The remote path incrementally syncs the project, transfers `.env.demo` and the
GEE key separately, builds the Compose services remotely, and verifies
`/health`. It does not expose the backend or frontend ports directly; the Nginx
proxy is the only public service.

For TLS, point a domain at the host and terminate HTTPS with a managed load
balancer or a reverse proxy in front of the demo host.
