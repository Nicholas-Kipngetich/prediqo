# Prediqo — C4 Architecture (Phase 0)

---

## Level 1 — System context

```mermaid
graph TD
    USER[Football fan<br/>Android user]
    ADMIN[Prediqo administrator]
    PROV[Football data provider<br/>API-Football / alternative]
    PLAY[Google Play<br/>Billing + Developer API]
    FIREBASE[Firebase<br/>Auth + Cloud Messaging]
    ADS[Google AdMob<br/>policy review required]

    USER -->|uses| APP[Prediqo Android app]
    ADMIN -->|manages| ADMINAPP[Prediqo Admin Dashboard]
    APP -->|REST API| API[Prediqo Backend]
    ADMINAPP -->|REST API| API
    API -->|fixtures, results, stats| PROV
    API -->|verify purchases| PLAY
    API -->|verify ID tokens, send push| FIREBASE
    APP -->|ID token + FCM| FIREBASE
    APP -->|ads, if enabled| ADS
```

**Key boundary:** The mobile app never calls the data provider or Google Play Developer
API directly. Provider keys and Play credentials stay server-side.

---

## Level 2 — Containers

```mermaid
graph TD
    subgraph Client
      MOBILE[Flutter Android app<br/>Riverpod + GoRouter + Dio]
      ADMINUI[Next.js admin dashboard]
    end

    subgraph "Local / self-hosted Docker stack"
      API[FastAPI backend<br/>REST /api/v1]
      WORKER[Celery worker<br/>sync, predictions, settlement, notifications]
      BEAT[Celery beat<br/>schedules]
      DB[(PostgreSQL 16)]
      CACHE[(Redis<br/>cache + broker + rate limits)]
      ML[MLflow + model artifacts<br/>self-hosted / filesystem]
    end

    subgraph External
      PROV[Football data API]
      FIREBASE[Firebase Auth + FCM]
      PLAY[Google Play Billing / Developer API]
      ADS[AdMob]
    end

    MOBILE --> API
    ADMINUI --> API
    API --> DB
    API --> CACHE
    API --> WORKER
    WORKER --> DB
    WORKER --> CACHE
    WORKER --> PROV
    WORKER --> ML
    BEAT --> WORKER
    API --> FIREBASE
    API --> PLAY
    MOBILE --> ADS
```

---

## Level 3 — Backend components (modular monolith)

```mermaid
graph TD
    ROUTER[API router /api/v1] --> AUTHM[Auth & identity module]
    ROUTER --> USERM[Users & profiles module]
    ROUTER --> SPORTM[Sports / competitions / teams / fixtures module]
    ROUTER --> STATM[Statistics module]
    ROUTER --> PREDM[Predictions module]
    ROUTER --> PERFM[Performance & settlement module]
    ROUTER --> TOKENM[Tokens & ledger module]
    ROUTER --> BILLM[Payments & subscriptions module]
    ROUTER --> NOTIFM[Notifications module]
    ROUTER --> ADMINM[Admin module]
    ROUTER --> CONFIGM[Config, feature flags & ad placements]

    AUTHM --> SEC[Security: token verification, RBAC, rate limits]
    ROUTER --> SEC

    SPORTM --> INGEST[Data ingestion & provider adapters]
    INGEST --> NORMALISE[Normalisation + validation + provenance]
    NORMALISE --> DB[(PostgreSQL)]

    PREDM --> ENGINE[AI inference engine<br/>Poisson / Elo / XGBoost / ensemble]
    ENGINE --> MLREG[Model registry + feature store snapshots]
    ENGINE --> EXPL[Explanation generator<br/>deterministic v1]
    PREDM --> SNAPSHOT[Immutable prediction snapshots]

    BILLM --> PLAYV[Play purchase verification + idempotency]
    TOKENM --> LEDGER[Append-only token ledger]
    SEC --> AUDIT[Audit log]
```

**Module boundary rule:** modules communicate through typed service interfaces and
database tables, never by importing each other's internal routers. This permits a future
split into separate services without rewriting domain logic.

---

## Level 3 — Mobile components

```mermaid
graph TD
    UI[Screens / widgets] --> STATE[Riverpod providers]
    STATE --> REPO[Repositories]
    REPO --> APIC[Centralised Dio client<br/>auth, retry, error mapping]
    REPO --> LOCAL[Hive TTL cache + secure storage]
    STATE --> DOMAIN[Domain models - Freezed]
    APIC --> ERR[Error/result types]
    UI --> DS[Design system components]
    UI --> NAV[GoRouter + deep links]
    APIC --> FCM[Firebase Messaging]
```

---

## Deployment view (local-first)

```mermaid
graph TD
    DEV[Developer PC - Windows] --> DOCKER[Docker Desktop + WSL2]
    DOCKER --> PG[postgres:16]
    DOCKER --> REDIS[redis:7]
    DOCKER --> API[FastAPI :8000]
    DOCKER --> WORKER[Celery worker + beat]
    DOCKER --> ADMIN[Admin dashboard :3000]
    DOCKER --> MLFLOW[MLflow :5000 - optional]
    DEV --> FLUTTER[Flutter SDK / Android emulator or device]
    FLUTTER -->|10.0.2.2:8000 emulator<br/>LAN IP for device| API
```

---

## Architecture principles

1. Single source of truth for entitlements: PostgreSQL.
2. All external data normalised and validated before entering domain models.
3. All long-running work asynchronous and idempotent.
4. Every write to tokens, predictions or admin actions is auditable.
5. Configuration via environment variables; no secrets in images or repositories.
6. Caching at API and client layers with explicit TTLs and stale-while-revalidate.
