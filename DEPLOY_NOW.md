# Deploy the demo

`deploy_now.sh` deploys the current Docker demo stack: the Next.js frontend,
FastAPI backend, Nginx proxy, model artifacts, and the configured Google Earth
Engine credential. It replaces the retired static `simple_api.py` deployment.

## One-time host setup

Use a Linux host with Docker Engine and the Docker Compose plugin installed.
The SSH account must be allowed to run `docker compose` without `sudo`, and the
host firewall/security group must allow inbound TCP port 80 (or the `DEMO_PORT`
you set below).

## Local configuration

Create `.env.demo` from the example and set the real values:

```bash
cp .env.demo.example .env.demo
```

Place the GEE service-account JSON key at `credentials/gee_key.json`. Both are
ignored by Git. Set `CORS_ORIGINS` to the public HTTP(S) origin you will use and
leave `DEMO_PORT=80` unless that port is already occupied.

## Deploy

```bash
./deploy_now.sh opc@YOUR_SERVER_IP
```

The optional second argument is a safe relative directory under that user's
home directory:

```bash
./deploy_now.sh opc@YOUR_SERVER_IP aquapredict-demo
```

The script incrementally syncs the project, transfers `.env.demo` and the GEE
key separately, builds the Compose services remotely, and verifies `/health`.
It does not expose the backend or frontend ports directly; the Nginx proxy is
the only public service.

For TLS, point a domain at the host and terminate HTTPS with a managed load
balancer or a reverse proxy in front of the demo host.
