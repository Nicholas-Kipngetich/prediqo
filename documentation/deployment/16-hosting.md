# Prediqo — Hosting & Deployment (Phase 11)

**No paid infrastructure is required for development or testing.** This phase documents
portable deployment choices; nothing here commits you to a paid service.

---

## 1. Current state

Everything runs locally with:

```powershell
docker compose up -d --build
```

Services: PostgreSQL 16, Redis 7, FastAPI backend, Celery worker + beat, Next.js admin
dashboard, optional MLflow (`--profile ml`). The Flutter app runs on the host and talks
to the API over `10.0.2.2:8000` (emulator) or your LAN IP (device).

---

## 2. Hosting options evaluated

| Option | Pros | Cons | Indicative cost | Decision |
|---|---|---|---|---|
| **Local only** | Free, full control | Not publicly reachable | $0 | Current |
| **Self-hosted Linux VPS** | Lowest predictable cost, Docker Compose reuse, full data control | You manage OS, backups, TLS, uptime | ~$10–30/mo | **Recommended first paid step** |
| **Render / Railway / Fly** | Fast deploy, managed runtime | Usage charges, cold starts/limits | ~$7–25/mo + managed DB | Good alternative |
| **Supabase (DB/backend)** | Managed Postgres, auth helpers | Vendor lock-in, free tier not for production | $0–25/mo | Optional |
| **AWS (ECS/RDS)** | Mature, scalable | Cost/complexity, needs expertise | Variable | Future only |

Prices are indicative and must be verified before commitment. Do not assume a free tier
is suitable for production.

---

## 3. Production-style Docker Compose

`infrastructure/deployment/docker-compose.prod.yml` is provider-neutral:

- PostgreSQL and Redis have **no host ports published** — reachable only inside the
  `prediqo` compose network.
- Backend, admin and MLflow bind to `127.0.0.1` only. Terminate TLS with a reverse proxy
  (Caddy or nginx) on the host.
- `ENVIRONMENT=production`, `AUTH_MODE=firebase`, `ALLOW_SAMPLE_DATA=false`.
- The provider and API key come from environment variables, never source code.

### VPS setup outline

```bash
git clone https://github.com/Nicholas-Kipngetich/prediqo.git
cd prediqo
cp .env.example .env
# Edit .env: strong POSTGRES_PASSWORD, SECRET_KEY, real FIREBASE_PROJECT_ID,
# service account path, FOOTBALL_DATA_PROVIDER=api-football and API key.

docker compose -f infrastructure/deployment/docker-compose.prod.yml up -d --build
docker compose -f infrastructure/deployment/docker-compose.prod.yml exec backend alembic upgrade head
```

Put a Caddyfile or nginx config in front of `127.0.0.1:8000` (API) and
`127.0.0.1:3000` (admin). Use Let's Encrypt for TLS. Do not expose PostgreSQL or Redis.

---

## 4. Environment variables

See `.env.example`. Production must set:

| Variable | Notes |
|---|---|
| `ENVIRONMENT` | `production` |
| `AUTH_MODE` | `firebase` — dev token mode is disabled |
| `SECRET_KEY` | Long random value |
| `POSTGRES_PASSWORD` | Strong, never committed |
| `FIREBASE_PROJECT_ID` | Firebase project |
| `FIREBASE_CREDENTIALS_PATH` | Service account JSON, mounted read-only |
| `FOOTBALL_DATA_PROVIDER` | `api-football` (licensed) |
| `FOOTBALL_DATA_API_KEY` | Provider key, server-side only |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | For purchase verification |
| `CORS_ORIGINS` | Explicit HTTPS origins only |
| `ADMIN_API_URL` | Public API URL for the admin dashboard build |

---

## 5. Backup and recovery

Scripts:

```powershell
# Windows / local dev
powershell -File infrastructure/scripts/backup.ps1
powershell -File infrastructure/scripts/restore.ps1 -BackupFile <file>
```

```bash
# Linux VPS
./infrastructure/scripts/backup.sh
./infrastructure/scripts/restore.sh ./backups/prediqo_....sql.gz
```

Verified locally: a SQLite dev backup was created and restored, preserving 1 user,
28 predictions and 3 notifications.

Targets (proposed, require approval):

| Metric | Target |
|---|---|
| Backup frequency | Nightly |
| Retention | 30 days rolling |
| RPO | 24 hours |
| RTO | 4 hours |
| Restore drill | Quarterly, documented |

The restore script prompts for `RESTORE` confirmation before replacing data.

---

## 6. Migration path to AWS or another cloud

1. Keep all configuration in env vars and `system_config`.
2. Docker images are portable; no cloud-specific SDK in business logic.
3. Alembic migrations work against any PostgreSQL host.
4. Replace the compose database with RDS/Supabase via `DATABASE_URL`.
5. Replace local volume storage with S3-compatible object storage for backups/artifacts.
6. Add autoscaling only when measured load justifies it.

---

## 7. Cost-control rules

- No paid service without documented justification and approval.
- Prefer a single VPS over multiple managed services at launch.
- Cache provider responses; monitor API usage against plan limits.
- Review provider licensing (including redistribution and ML training rights) before
  switching from sample data to real data.
