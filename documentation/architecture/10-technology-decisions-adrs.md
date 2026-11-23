# Prediqo — Architecture Decision Records (Phase 0)

Each ADR records a decision, its rationale, alternatives and consequences.

---

## ADR-001 — Product name is Prediqo
- **Status:** Accepted (pending confirmation)
- **Context:** Spec says "PredictPro"; build instruction says "use this name Prediqo".
- **Decision:** Canonical brand and all code/config identifiers use `prediqo`.
- **Alternatives:** Keep PredictPro (rejected — contradicts explicit instruction).
- **Consequences:** Trademark check required; all docs/code use one name.

## ADR-002 — Modular monolith backend, no microservices
- **Status:** Accepted
- **Context:** 10k users / 1k DAU planning target; small team; local-first constraint.
- **Decision:** Single FastAPI app with enforced module boundaries (auth, users, sports,
  predictions, tokens, payments, notifications, admin, config). Celery workers for async work.
- **Alternatives:** Microservices, serverless functions — higher ops cost, no benefit at this scale.
- **Consequences:** Need discipline on module boundaries; future extraction is possible.

## ADR-003 — Firebase for identity, PostgreSQL for entitlements
- **Status:** Accepted
- **Context:** Need email + Google sign-in and backend RBAC/entitlements.
- **Decision:** Firebase Auth issues ID tokens; backend verifies them and looks up user roles,
  VIP status and token balance in PostgreSQL on every protected request.
- **Alternatives:** Firebase custom claims as source of truth (rejected — drift risk);
  home-grown auth (rejected — security cost).
- **Consequences:** One extra DB lookup per request (cached briefly); entitlement changes
  take effect immediately.

## ADR-004 — Statistical ensemble, not LLM, generates probabilities
- **Status:** Accepted
- **Context:** Need accurate, explainable, reproducible probabilities.
- **Decision:** Poisson (+ Dixon–Coles), Elo, XGBoost combined with validation-optimised
  weights and calibration. Model versions tracked in DB and MLflow.
- **Alternatives:** LLM numeric predictions (rejected — unreliable, non-reproducible).
- **Consequences:** Requires historical data, validation discipline and monitoring.

## ADR-005 — Deterministic explanations in v1
- **Status:** Accepted
- **Context:** "LLM must never invent statistics" and cost/reliability concerns.
- **Decision:** Render explanations from structured facts used by the model. Optional LLM
  reformulation deferred, with strict grounding if ever added.
- **Alternatives:** Free-form LLM in v1 (rejected — fabrication risk).
- **Consequences:** Less fluent prose; zero fabrication risk and lower cost.

## ADR-006 — Play purchase verification via polling, not Pub/Sub
- **Status:** Accepted
- **Context:** Need purchase verification and subscription events without paid GCP streaming.
- **Decision:** Backend verifies purchase tokens with Google Play Developer API at purchase
  time; Celery Beat periodically reconciles purchases/subscriptions (RTDN optional later).
- **Alternatives:** Real-time Developer Notifications via Pub/Sub (rejected for launch — cost/complexity).
- **Consequences:** Slight delay in entitlement sync; mitigated by immediate verification call.

## ADR-007 — Append-only token ledger with DB-enforced non-negative balance
- **Status:** Accepted
- **Context:** Immutable transaction history, no double credit/debit.
- **Decision:** `token_transactions` append-only; balance updated atomically with row lock;
  unique idempotency keys and purchase tokens; CHECK constraint; refunds/adjustments are
  compensating entries.
- **Alternatives:** Mutable balance column only (rejected — unauditable).
- **Consequences:** Slightly more storage; strong financial integrity.

## ADR-008 — Provider abstraction with normalisation and provenance
- **Status:** Accepted
- **Context:** Provider licensing/cost may change; data quality varies.
- **Decision:** Adapter interface per provider; normalised domain models; validation and
  provenance metadata; missing data remains null.
- **Alternatives:** Couple to one provider SDK (rejected — lock-in).
- **Consequences:** Extra mapping layer; future provider switch is low-cost.

## ADR-009 — Client TTL cache with stale-while-revalidate
- **Status:** Accepted
- **Context:** "Offline-friendly" requirement; flaky mobile networks in target markets.
- **Decision:** Hive TTL cache on device + Redis cache on server; show stale data with a
  freshness label while refreshing; explicit offline/error states.
- **Alternatives:** Full offline database (overkill for v1); no cache (poor UX).
- **Consequences:** Need cache invalidation rules and freshness display.

## ADR-010 — Self-hosted MLflow on filesystem
- **Status:** Accepted
- **Context:** Experiment tracking without cloud cost.
- **Decision:** MLflow file store locally; model artifacts on disk/volume; metadata mirrored
  into `model_versions` and `model_evaluations` tables.
- **Alternatives:** Managed ML platform (rejected — cost).
- **Consequences:** Need volume backups; no hosted UI outside the network.

## ADR-011 — Flutter stack: Riverpod + GoRouter + Dio + Freezed
- **Status:** Accepted
- **Context:** Maintainable, typed state and navigation.
- **Decision:** Riverpod for state, GoRouter for routing/deep links, Dio for HTTP with
  centralised interceptors, Freezed for immutable models, fl_chart for charts,
  flutter_secure_storage for secrets, intl for localisation.
- **Alternatives:** Provider/bloc (viable), GetX (rejected — less type-safe/opinionated).
- **Consequences:** Code generation step; consistent patterns required.

## ADR-012 — Dark-first Material 3 design system
- **Status:** Accepted
- **Context:** Premium data-driven identity; light mode required.
- **Decision:** Deep charcoal/black + neon green accent, theme tokens in one place,
  reusable components, no per-screen hard-coded styling.
- **Consequences:** Design-system maintenance overhead; consistency payoff.

## ADR-013 — Local-first infrastructure, cloud optional
- **Status:** Accepted
- **Context:** No assumed cloud account or budget.
- **Decision:** Docker Compose for all services; env-based config; deployment options
  documented from self-hosted VPS upward; no provider-specific code.
- **Consequences:** Developer must install Docker/Flutter locally; ops responsibility on VPS.

## ADR-014 — Ads disabled by default, allow-listed and remotely configurable
- **Status:** Accepted
- **Context:** AdMob policy scrutiny for prediction apps; VIP ad-free promise.
- **Decision:** `ad_placements.enabled = false` initially; non-betting allow-list;
  frequency caps; excluded from purchase/unlock flows; excluded for VIP.
- **Alternatives:** Enable all formats immediately (rejected — policy/compliance risk).
- **Consequences:** Ad revenue deferred until review passes.

## ADR-015 — Immutable prediction snapshots and append-only corrections
- **Status:** Accepted
- **Context:** Honest performance reporting; corrections must be auditable.
- **Decision:** Predictions and settlements are immutable; corrections are superseding
  records with reason and actor; history never deleted.
- **Consequences:** Analytics must account for supersedes chains.
