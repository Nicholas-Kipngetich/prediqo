# Prediqo — Cost Estimates (Phase 0)

**Important:** all figures are indicative planning ranges, not quotes. Verify current
pricing before committing. **No paid service will be introduced without explicit
approval.** Free/low-cost alternatives are listed first.

---

## 1. One-time costs

| Item | Cost | Notes |
|---|---|---|
| Git / GitHub | $0 | Free private repo suitable for source control. |
| Flutter SDK, Android Studio, Docker Desktop, VS Code | $0 | Docker Desktop free for personal use — verify licence for commercial use. |
| Domain (optional, e.g. `prediqo.<tld>`) | ~$10–20/year | Optional for local/dev; needed for public API/web. |
| **Google Play developer account** | **~$25 one-time** | Required to publish Android app. Needs approval. |
| Trademark search (optional) | $0–300 | Voluntary due diligence on "Prediqo" name. |

---

## 2. Monthly running costs — scenarios

### Scenario A — Local development only (Phases 1–10)
| Item | Cost |
|---|---|
| PostgreSQL, Redis, FastAPI, Celery, MLflow, admin dashboard (Docker Compose) | $0 |
| Flutter, Android emulator / physical device | $0 |
| GitHub Actions CI (small OSS/private usage) | $0 |
| Firebase Auth + FCM (Spark/free tier at target scale) | $0 (verify quotas) |
| Football data provider free tier | $0 but **insufficient** for commercial product |
| **Subtotal** | **$0**, but not usable for real production data |

### Scenario B — Low-cost public launch (recommended first paid step)
| Item | Indicative monthly |
|---|---|
| Self-hosted VPS (2–4 vCPU, 4–8 GB RAM) with Docker, PostgreSQL, Redis | $10–30 |
| Paid football data API (commercial licence) | $20–150 (verify plan + rights) |
| Firebase (Auth/FCM, likely free tier) | $0–10 |
| Domain | ~$1–2 |
| Monitoring (optional free tier) | $0 |
| Object storage for backups/model artifacts (optional) | $0–5 |
| **Subtotal** | **~$31–197/month** (plus Play commission on revenue) |

### Scenario C — Managed PaaS launch (higher cost, less ops)
| Item | Indicative monthly |
|---|---|
| App hosting (Render/Railway/Fly) | $7–25 |
| Managed PostgreSQL (Supabase/Render/Railway) | $0–25 |
| Managed Redis | $0–10 |
| Football data API | $20–150 |
| **Subtotal** | **~$27–210/month** |

### Scenario D — Growth / future AWS (only after traction)
- Expect materially higher cost; revisit once 10k+ DAU or paying subscribers justify it.
- No commitment now. Migration path documented in `12-local-development-and-hosting.md`.

---

## 3. Revenue-side platform fees

- Google Play Billing commission: typically ~15–30% of in-app purchases/subscriptions
  (rate depends on programme and subscription duration). Verify current rates.
- AdMob revenue: variable and unpredictable; may be restricted for prediction apps
  under gambling-adjacent policy. **Do not build a financial model on ad revenue.**
- Prices must account for platform fees, data API cost and VAT/tax where applicable.

---

## 4. Cost-control rules

1. Start on Scenario A; move to B only when public access is required.
2. Prefer self-hosted VPS over managed services where ops capacity allows.
3. Avoid GCP Pub/Sub/RTDN at launch — use Play Developer API polling via Celery.
4. Cache provider responses to reduce API call volume.
5. Self-host MLflow on local filesystem/volume; no managed ML platform.
6. Use free tiers for Firebase, CI and monitoring within quotas; alert before overage.
7. Every new paid dependency requires a documented justification and approval.

---

## 5. Approval requests

- [ ] Approve Google Play developer account (~$25 one-time).
- [ ] Approve a monthly budget range for a licensed football data provider (Scenario B).
- [ ] Choose Scenario B (self-hosted VPS) vs C (managed PaaS) for public launch.
- [ ] Confirm no paid service is to be used during local development.
