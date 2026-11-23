# Prediqo — Phase 0 Executive Summary

**Status:** Phase 0 complete — awaiting approval before Phase 1.
**Date:** 2026-11-23
**Product:** Prediqo (AI-powered football intelligence platform)
**Tagline:** Predict Smarter. Understand Deeper.

---

## 0.1 Important naming decision

The source specification repeatedly uses the name **PredictPro**, but the instruction
for this build explicitly says: *"use this name Prediqo"*.

**Decision applied throughout this documentation set:** the product is **Prediqo**.

| Item | Canonical value |
|---|---|
| Brand / display name | Prediqo |
| Tagline | Predict Smarter. Understand Deeper. |
| Repository | `prediqo` |
| Backend Python package | `prediqo` |
| Mobile Dart package / app | `prediqo` |
| Android application id | `com.prediqo.app` |
| Database | `prediqo` |
| Primary domain (when acquired) | `prediqo.<tld>` |

All occurrences of "PredictPro" in the source brief should be read as "Prediqo".
A trademark/name availability check is an open Phase 0 action (see §0.6).

---

## 0.2 Repository inspection result

| Check | Result |
|---|---|
| Directory contents | Empty |
| Git repository | None |
| `git` | Available (`C:\Program Files\Git\cmd\git.exe`) |
| `python` | Available (Windows Store shim — verify real interpreter in Phase 1) |
| `node` / `npm` | Available |
| `docker` | **Not installed** |
| `flutter` | **Not installed** |
| `psql` | **Not installed** |

Implication: Phase 1 tooling installation (Flutter SDK, Docker Desktop with WSL2,
PostgreSQL client, Android Studio) is a prerequisite and carries no software licence
cost except the Google Play developer account and any paid data provider.

---

## 0.3 Deliverables produced in Phase 0

| # | Deliverable | File |
|---|---|---|
| 1 | Product Requirements Document (functional + non-functional) | `documentation/01-product-requirements.md` |
| 2 | User journeys + UI navigation map | `documentation/02-user-journeys-and-navigation.md` |
| 3 | C4 architecture diagrams | `documentation/architecture/03-c4-architecture.md` |
| 4 | Database ERD | `documentation/database/04-database-erd.md` |
| 5 | API contracts | `documentation/api/05-api-specification.md` |
| 6 | AI/ML architecture and validation plan | `documentation/ai-ml/06-ai-ml-architecture.md` |
| 7 | Sports data provider evaluation | `documentation/architecture/07-sports-data-providers.md` |
| 8 | Security threat model | `documentation/security/08-security-threat-model.md` |
| 9 | Cost estimates | `documentation/deployment/09-cost-estimates.md` |
| 10 | Technology decisions / ADRs | `documentation/architecture/10-technology-decisions-adrs.md` |
| 11 | Technical risk register | `documentation/architecture/11-risk-register.md` |
| 12 | Local development + optional hosting | `documentation/deployment/12-local-development-and-hosting.md` |
| 13 | Phased roadmap | `documentation/13-phase-roadmap.md` |
| 14 | Repository bootstrap instructions | `documentation/repository-bootstrap.md` |

---

## 0.4 Contradictions and ambiguities found in the brief

These must be resolved before or during Phase 1. Each has a recommended resolution.

| ID | Issue | Type | Recommended resolution |
|---|---|---|---|
| C-01 | Product named "PredictPro" in spec vs "Prediqo" in build instruction | Contradiction | Use **Prediqo** everywhere (applied). Confirm. |
| C-02 | Guest access "depending on final access policy" — policy never defined | Missing decision | Guests may browse fixtures and see 1 free prediction/day; registration required for history, preferences, tokens, VIP. |
| C-03 | "Free plan includes advertisements" + "VIP ad-free" + "do not show ads during critical interactions" + "football prediction apps may face gambling ad scrutiny" | Policy tension | Ads from a vetted, non-betting allow-list only; frequency-capped; disabled during purchase/prediction-unlock flows; VIP excluded; **activation blocked pending legal/policy review**. |
| C-04 | "Use Google Play Billing" + "refund events" + no cloud budget | Cost/tension | Use Play Developer API polling via Celery for v1 (no Pub/Sub/RTDN) to avoid paid GCP streaming; add RTDN later. |
| C-05 | "AI-generated explanations" + "LLM must never invent statistics" | Feasibility | v1 explanations are deterministic templates rendered from verified model facts; optional LLM layer added later with strict grounding and numeric validation. |
| C-06 | "Immutable prediction history" + "account deletion" + "corrections must be auditable" | Legal tension | Prediction records are non-personal analytics and remain pseudonymised; user linkage is anonymised on deletion; corrections are append-only superseding records. |
| C-07 | "Never charge twice for a feature in VIP" | Undefined flow | Entitlement resolution order: VIP → token unlock. Check entitlement before showing unlock prompt; if a token unlock already occurred, record a compensating transaction per published refund policy. |
| C-08 | "Corners analysis" + "xG" + "lineups/injuries" but also "missing data must remain missing" | Data availability | Only markets with provider coverage and validated models ship at launch; others show an explicit "Insufficient data" state, never estimated placeholders. |
| C-09 | "10,000 users / 1,000 DAU targets" vs "do not claim tested capacity" | Wording | Treat as capacity-planning assumptions; record load-test results before making any capacity claim. |
| C-10 | "Current target API requirements" | Time-sensitive | Verify Play target API level at release time; do not hard-code an unverified value now. |

---

## 0.5 Missing requirements (must be supplied before Phase 1/2)

1. **Data provider budget approval** — real fixtures/results require a licensed paid
   API. This is the single hardest blocker for Phase 3+.
2. **Concrete free-tier limits** — e.g. "3 free predictions/day", "1 free full
   analysis/week". Needs product decision.
3. **Token package prices, token cost per report, VIP entitlement matrix** — exact
   numbers, currencies per market (KSh, ZAR, NGN, GHS, GBP).
4. **Android compatibility floor** — `minSdk`, target devices, 32/64-bit requirements.
5. **Locales** — English first; Swahili, Afrikaans, Hausa, Yoruba, Igbo candidates.
6. **Legal entity** owning Terms, Privacy Policy, and Play developer account.
7. **Trademark/name availability** check for "Prediqo".
8. **Model publication thresholds** — minimum sample sizes, minimum calibration
   quality, suppression rules.
9. **Scoring rules** — what counts as a "correct" probabilistic prediction
   (recommended: Brier score primary, argmax accuracy secondary).
10. **Settlement source of truth** and dispute process.
11. **Data retention periods** and backup retention (proposed: 30-day rolling DB
    backups, 90-day logs, 12-month audit logs — needs approval).
12. **Team/resources and target dates** for Phases 1–12.
13. **Initial admin accounts** and super-admin designation.
14. **Logo/brand assets** — must be original; no copyrighted graphics.
15. **AdMob account eligibility** and legal review of gambling-adjacent policy.

---

## 0.6 Validated technology stack (summary)

Full rationale in `documentation/architecture/10-technology-decisions-adrs.md`.

- **Mobile:** Flutter (Dart), Material 3, Riverpod, GoRouter, Dio, Freezed,
  flutter_secure_storage, Hive (TTL cache), fl_chart, firebase_messaging, intl.
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic,
  PostgreSQL 16, Redis, Celery + Celery Beat, pytest, Ruff, mypy.
- **AI/ML:** NumPy, Pandas, SciPy, scikit-learn, XGBoost, MLflow (self-hosted),
  Poisson + Dixon–Coles + Elo + XGBoost ensemble, calibrated probabilities.
- **Admin:** React + Next.js + TypeScript + Tailwind CSS.
- **Infra:** Docker Compose, local-first, no mandatory cloud.
- **Cloud-optional:** self-hosted VPS → low-cost PaaS → managed DB → AWS later.

**Not chosen (deliberately):** microservices, Kubernetes, managed ML platforms,
client-side purchase trust, LLM as numeric engine, hardcoded ad units.

---

## 0.7 Key architectural trade-offs (principal-engineer view)

1. **Modular monolith over microservices.** At 1,000 DAU, microservices add
   operational cost without benefit. Module boundaries are enforced in code so a
   future split is possible.
2. **Database is the entitlement source of truth.** Firebase handles identity; it
   does not decide who is VIP. Backend checks DB on every protected request.
3. **No LLM in the numeric path.** Poisson/Elo/XGBoost produce all probabilities;
   an LLM (if ever used) only reformats already-verified facts.
4. **Explainable by construction.** v1 explanations are generated from the same
   structured feature/prediction object the model used, so fabrication is impossible.
5. **Append-only ledgers** for tokens, prediction snapshots, and audit logs.
   Corrections are compensating records, never in-place edits.
6. **Provider abstraction.** All data enters through a normalisation layer; a provider
   switch does not touch the prediction engine.
7. **Polling before Pub/Sub.** Purchase verification via scheduled Play API polling
   avoids a paid GCP dependency at launch.
8. **Ads are off by default** until policy review passes and remote config enables them.

---

## 0.8 Approval gate

Phase 1 (`documentation/13-phase-roadmap.md`) **has not started**. Approval is requested
for:

- [ ] Product name **Prediqo** confirmed.
- [ ] Phase 0 architecture and ADRs accepted.
- [ ] Data provider selection and budget (see `07-sports-data-providers.md`).
- [ ] Free-tier limits, token pricing, VIP entitlement matrix supplied.
- [ ] Legal/policy review path for ads and prediction language agreed.
- [ ] Repository bootstrap authorised (§`repository-bootstrap.md`).

Awaiting your go-ahead before any application code is written.
