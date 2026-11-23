# Prediqo

**Predict Smarter. Understand Deeper.**

AI-powered football analytics and prediction platform. Prediqo is an informational
sports analytics product — **not** a bookmaker. No wagering, deposits, withdrawals,
betting wallets, payouts or bookmaker account management.

Repository: https://github.com/Nicholas-Kipngetich/prediqo.git

---

## Status

| Phase | Status |
|---|---|
| 0 — Product discovery & architecture | ✅ Complete (`documentation/`) |
| 1 — Project foundation | ✅ Scaffolded and verified |
| 2 — Backend & authentication | ✅ Complete (16 tests, CI green) |
| 3 — Sports data integration | ✅ Complete (22 tests); provider licence decision pending |
| 4 — Mobile application UI | ✅ Complete (design system, navigation, core screens; Flutter CI green) |
| 5 — AI prediction engine | ✅ Complete (Poisson/Dixon–Coles + Elo + calibrated ensemble; 32 tests green) |
| 6 — Analytics | ✅ Complete (30 backend tests; settlement + performance verified live) |
| 7 — Tokens & VIP | ✅ Complete (35 tests; purchase + VIP entitlement verified live) |
| 8–12 | ⏳ Not started |

### Phase 1 verification results (2026-11-23)

| Check | Result |
|---|---|
| `pytest -q` | ✅ 3 passed |
| `ruff check app tests` | ✅ All checks passed |
| `ruff format --check app tests` | ✅ 13 files formatted |
| `mypy app` | ✅ No issues in 12 source files |
| `npm run build` (admin dashboard) | ✅ Compiled and static pages generated |
| `docker-compose.yml` parse | ✅ 7 services, 3 volumes |
| Flutter CI (`pub get`, `analyze`, `format`, `test`) | ✅ passes on `main` and `develop` (Flutter 3.50.1 / Dart 3.13) |

> **Windows note:** this machine's Application Control policy blocks some compiled
> Python extensions (`.pyd`). SQLAlchemy is therefore pinned to `<2.1`, which has a
> pure-Python fallback, and mypy is installed from source. On Linux CI these
> workarounds are unnecessary but harmless. The database engine is created lazily so
> importing the app never requires a live driver; `/health` reports `db: unavailable`
> until PostgreSQL is reachable.

Phase 0 deliverables (PRD, C4 diagrams, ERD, API spec, AI/ML architecture, provider
evaluation, threat model, cost estimates, ADRs, risk register, roadmap) are in
[`documentation/`](documentation/00-phase0-executive-summary.md).

---

## Repository layout

```
prediqo/
├── mobile/              Flutter Android app (Riverpod, GoRouter, Dio)
├── backend/             FastAPI modular monolith + Celery + Alembic
├── ai-engine/           Statistical / ML prediction engine (Phase 5)
├── admin-dashboard/     React + Next.js admin platform (Phase 9)
├── infrastructure/      Docker, deployment, scripts
├── documentation/       Phase 0 discovery and all architecture docs
├── .github/workflows/   CI pipelines
├── docker-compose.yml   Local development stack
├── .env.example         Environment template (copy to .env; never commit .env)
└── README.md
```

---

## Prerequisites (Windows)

Install the following before running the stack:

| Tool | Purpose | Status on dev machine |
|---|---|---|
| Git | Source control | ✅ installed |
| Node.js 20+ | Admin dashboard | ✅ installed |
| Python 3.12+ | Backend / AI engine | ✅ installed via winget |
| Docker Desktop + WSL2 | PostgreSQL, Redis, services | ❌ install required |
| Flutter SDK (stable) | Android app | ❌ install required |
| Android Studio + SDK | Android emulator / build | ❌ install required |
| GitHub CLI (optional) | `gh` auth / PRs | installed, not authenticated |

> The `python` command on PATH may still resolve to the Microsoft Store stub.
> Use the full path until your PATH refreshes:
> `$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"`

---

## Quick start

### 1. Environment

```powershell
Copy-Item .env.example .env
# Edit .env — never commit it (it is gitignored)
```

### 2. Backend (local venv, without Docker)

```powershell
cd backend
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -v
python -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health and http://localhost:8000/docs.

### 3. Full stack with Docker (after installing Docker Desktop)

```powershell
docker compose up -d --build
docker compose logs -f backend celery-worker
```

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Admin dashboard | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| MLflow (optional) | `docker compose --profile ml up -d` → http://localhost:5000 |

### 4. Flutter app

See [`mobile/README.md`](mobile/README.md). First run `flutter create . --platforms android`
inside `mobile/` to generate platform folders, then:

```powershell
flutter pub get
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### 5. Admin dashboard

```powershell
cd admin-dashboard
npm ci
npm run dev
```

---

## Branching

`main` (protected) ← PR ← `develop` ← PR ← `feature/*`, `bugfix/*`, `release/*`.

Currently both `main` and `develop` exist on the remote.

---

## Open decisions before Phase 2+

1. Licensed football data provider and monthly budget (blocker for Phase 3).
2. Concrete free-tier daily limits.
3. Token package prices and per-report unlock cost.
4. VIP monthly/annual price and entitlement matrix.
5. AdMob legal/policy review path.
6. Android `minSdk` / target API and locales.

See `documentation/00-phase0-executive-summary.md` §0.5.

---

## Governance

- Task statuses: Not started · In progress · Blocked · Implemented · Tested · Accepted.
- No fabricated sports data, no hardcoded secrets, no unexplained placeholders.
- No paid service without documented justification and approval.
- Every architectural decision is recorded in `documentation/architecture/10-technology-decisions-adrs.md`.
