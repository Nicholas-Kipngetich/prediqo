# Prediqo — Phased Implementation Roadmap (Phase 0)

Effort estimates are relative planning figures, not commitments. Each phase has an exit
gate; the next phase starts only after acceptance.

---

## Phase 0 — Product discovery & architecture ✅ COMPLETE (awaiting approval)
**Deliverables:** this document set.
**Exit gate:** approval of name, architecture, ADRs, data provider decision, pricing/limits,
ads policy path, repository bootstrap.
**Status:** Implemented (docs), pending Accepted.

## Phase 1 — Project foundation
**Deliverables:** GitHub repo + branches, Flutter project, FastAPI project, PostgreSQL,
Docker Compose, env config, CI pipeline, README, Windows setup instructions.
**Exit gate:** all services run locally; Flutter app builds and calls `/health`; CI green.
**Dependencies:** Phase 0 approval; install Flutter/Docker/Python.
**Note:** local `git init` already done.

## Phase 2 — Backend & authentication
**Deliverables:** DB schema + Alembic migrations, Firebase token verification, users,
profiles, RBAC, API foundation, error handling, OpenAPI.
**Exit gate:** auth tests pass; RBAC verified; migrations apply cleanly.

## Phase 3 — Sports data integration
**Deliverables:** provider adapter, competitions, teams, fixtures, results, statistics,
synchronisation, validation, provenance, caching.
**Exit gate:** real fixtures visible in API; sync jobs monitored; no fabricated fields.
**Blocker:** provider licence + budget approval.

## Phase 4 — Mobile application UI
**Deliverables:** branding/design system, navigation, home, discovery, trending, match
analysis, profile; real backend data where available.
**Exit gate:** widget/navigation tests pass; dark+light themes; responsive layouts.

## Phase 5 — AI prediction engine
**Deliverables:** data processing, features, Poisson/Dixon–Coles, Elo, XGBoost, ensemble,
calibration, evaluation, publication with immutable snapshots.
**Exit gate:** validation metrics recorded; leakage tests pass; suppression rules active;
no prediction published below thresholds.

## Phase 6 — Analytics
**Deliverables:** prediction history, settlement rules, performance reporting, charts,
model analytics.
**Exit gate:** settlement tests pass; history immutable; sample sizes always shown.

## Phase 7 — Tokens & VIP
**Deliverables:** token ledger, packages, Play purchase verification, subscriptions,
VIP entitlements, restore purchases, refunds, audit logs.
**Exit gate:** concurrency/replay tests pass; no double credit; entitlements correct.

## Phase 8 — Advertising
**Deliverables:** AdMob SDK, allow-listed placements, frequency caps, consent, VIP ad-free.
**Exit gate:** **legal/policy review passed**; test ad units only; activation approved.
**May be deferred** if policy review is unfavourable.

## Phase 9 — Admin dashboard
**Deliverables:** React/Next.js admin: users, sports, predictions, monetisation, system
health, model performance, audit logs.
**Exit gate:** all sensitive operations authorised + audited; admin tests pass.

## Phase 10 — Notifications
**Deliverables:** FCM, scheduling, preferences, deep links, dedupe.
**Exit gate:** notifications delivered in correct timezone; duplicates prevented.

## Phase 11 — Hosting & deployment
**Deliverables:** full local verification, then choose self-hosted VPS or low-cost PaaS;
deployment docs; backup/restore scripts. No AWS requirement.
**Exit gate:** public deployment reachable; HTTPS; backups verified.

## Phase 12 — Production readiness
**Deliverables:** full test suite, security review, performance/load validation, privacy
docs, backup drill, purchase verification, release candidate, Google Play assets.
**Exit gate:** all 21 final acceptance criteria from the brief demonstrated with tests
and verifiable results.

---

## Cross-cutting rules

- No phase is "complete" because code was generated — it must be tested and verified.
- Task tracker statuses: Not started → In progress → Blocked → Implemented → Tested → Accepted.
- Every ADR change requires a new ADR, not an edit of history.
- No fabricated sports data, no hardcoded secrets, no unexplained placeholders.
- Paid services only after explicit approval (data API, Play account, hosting).
