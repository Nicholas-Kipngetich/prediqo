# Infrastructure

- Root `docker-compose.yml` defines the local development stack.
- `backend/Dockerfile` builds the FastAPI application and Celery workers.
- `admin-dashboard/Dockerfile` builds the Next.js admin dashboard.
- `deployment/` will hold VPS/PaaS deployment manifests in Phase 11.
- `scripts/` will hold backup and restore scripts in Phase 11.

Start the stack from the repository root:

```powershell
docker compose up -d --build
```
