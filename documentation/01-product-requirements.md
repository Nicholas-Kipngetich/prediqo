# Prediqo — Product Requirements Document (Phase 0)

**Version:** 0.1 (draft for approval)
**Status:** Discovery complete, pending sign-off

---

## 1. Product definition

Prediqo is an informational football analytics and prediction platform for Android.
It helps users understand upcoming matches using real data, statistical models and
explainable probabilities. It is **not** a bookmaker: no wagering, deposits,
withdrawals, betting wallets, payouts or bookmaker account management.

- **Vision:** modern, premium football intelligence that is transparent and data-driven.
- **Tagline:** Predict Smarter. Understand Deeper.
- **Primary platform:** Android (Flutter).
- **Initial sport:** Football (Assoc. Soccer). Basketball, tennis, cricket and American
  football are future extensions behind a `sport_id` abstraction.
- **Target markets:** Kenya, UK, South Africa, Nigeria, Ghana, international.

---

## 2. Functional requirements

### FR-01 User types & access

| Role | Capabilities |
|---|---|
| Guest | Browse selected fixtures, view limited match info, 1 free prediction/day, explore UI. Cannot save preferences, history, tokens or VIP. |
| Free (registered) | Fixture browsing, selected predictions, basic analysis, selected stats, trending, limited history, selected notifications, rewarded ads, token purchase, VIP upgrade. |
| Token user | All Free capabilities + unlock individual premium reports with tokens. |
| VIP user | Expanded daily predictions, advanced analysis, more markets, detailed explanations, extended history, advanced performance analytics, personalised alerts, premium reports, ad-free, optional monthly tokens. |
| Admin | Manage users, sports data, fixtures, predictions, model versions, token packages, subscription plans, config, notifications, analytics, audit logs. |
| Super Admin | All Admin capabilities + role management and irreversible system operations. |

**FR-01.1** Entitlements must be enforced on the backend for every protected endpoint.
Hiding a button in Flutter is not authorisation.
**FR-01.2** Entitlement resolution order: active VIP → included in plan (free); else
token unlock; else unlock prompt. Never charge tokens for a feature already covered by
VIP.

### FR-02 Onboarding & splash
- Splash shows logo + tagline, restores session, initialises services, with timeout and
  retry (no infinite loader).
- Onboarding explains purpose, probability interpretation, free/token/VIP access,
  responsible use and privacy. Skippable; completion flag persisted.

### FR-03 Home dashboard
- Personalised greeting, current date (user timezone), token balance, VIP status.
- Today's featured matches, today's predictions, trending fixtures, upcoming matches,
  recent results, recommended analysis, favourite competitions.
- Search + filters. Ad slot for free users only (remote-configurable, frequency-capped).
- Match cards show competition, teams, logos (licensed or initials fallback), kickoff
  in local time, status, H/D/A probabilities, analysis availability, premium marker.

### FR-04 Match discovery
- Filters: Today, Tomorrow, Yesterday, Upcoming, This week, calendar date, country,
  competition, team, status.
- Search, competition sections with expandable league lists, date navigation,
  incremental/paginated loading.
- All timestamps stored UTC, converted for display using user-selected timezone.

### FR-05 Trending matches
- Ranking from real signals (user interest, competition popularity, importance, data
  availability, model coverage). Must not fabricate popularity numbers and must not be
  presented as prediction confidence.

### FR-06 Detailed match analysis
For each fixture: overview, 1X2 probabilities, goals analysis (xG, O/U thresholds,
BTTS, correct-score distribution), corners (only if provider data exists), team form,
head-to-head, advanced intelligence (xG, clean sheets, first half, strength ratings,
rest days, lineups/injuries where verified), AI explanation, premium preview + unlock.

**FR-06.1** Probabilities for mutually exclusive outcomes must sum to ~100% after
rounding (largest-remainder rounding).
**FR-06.2** Missing data renders an explicit "Insufficient verified data" state.
**FR-06.3** All analysis displays data-as-of timestamp and source/provenance.
**FR-06.4** Lineups/injuries/xG are never fabricated by the LLM or the client.

### FR-07 Predictions feed
Organised by market: result, double chance, goals, BTTS, corners, first half, other
validated markets. Each item shows fixture, market, probability, publication time,
model version, data freshness, explanation, status. Filters: date, competition, market,
status.

### FR-08 Performance centre
Totals (total/settled/correct/incorrect/pending/void), accuracy, breakdowns by
competition, market, week, month, calibration curve, model comparisons. **Always show
sample sizes. Never delete losing predictions. Never alter history. Distinguish
prediction accuracy from financial return.**

### FR-09 Prediction history
Statuses: pending, correct, incorrect, void, postponed, abandoned. Search + filters
(date, competition, market). Records preserved immutably.

### FR-10 VIP membership
Benefits, monthly/annual pricing, comparison, ad-free, purchase flow, status, renewal
date, restore purchases, manage/cancel subscription. Transparent pricing.

### FR-11 Token store
Balance, packages, prices, unlock costs, purchase history, transaction history.
Confirmation dialog before deduction. Duplicate-purchase and double-deduction
prevention. All purchases verified by backend; Google Play Billing for digital goods.

### FR-12 Notifications
Daily insights, upcoming fixtures, favourite team updates, results, VIP content,
subscription events; configurable preferences, timezone-aware, deduplicated.

### FR-13 Profile & settings
User info, favourite teams/competitions, timezone, theme (dark default + light),
notifications, token balance, VIP status, privacy, account deletion, support, T&Cs.

### FR-14 Admin dashboard
Business dashboard; user management; sports management; prediction management;
monetisation management; system health, failed jobs, provider sync, model performance,
audit logs. Every sensitive operation authorised and audited.

### FR-15 Prediction lifecycle
Retrieve fixture → validate → normalise → build as-of features → run models → validate
probabilities → generate explanation → publish → immutable snapshot → fetch result →
settle → update analytics. Corrections are append-only and auditable. Defined rules for
postponed, abandoned, cancelled and rescheduled fixtures.

---

## 3. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | p95 cached API < 500 ms under agreed test load (target: 1,000 DAU). Must be load-tested before any capacity claim. |
| NFR-02 | Availability | Graceful degradation when provider is down; stale-while-revalidate cache; no infinite loading. |
| NFR-03 | Security | HTTPS only; Firebase ID token verification; backend RBAC; input validation; rate limiting; secret management; audit logs; no secrets in repo. |
| NFR-04 | Privacy | Data minimisation; timezone/preferences local where possible; account deletion with pseudonymised analytics; privacy policy and Data Safety declaration. |
| NFR-05 | Maintainability | Modular boundaries, SOLID, DI, type safety, formatting, linting, ADRs, >70% backend unit test coverage target. |
| NFR-06 | Portability | Docker Compose local stack; env-based config; no provider lock-in; no mandatory cloud. |
| NFR-07 | Cost | No paid service without documented justification and approval. Free/low-cost alternatives evaluated first. |
| NFR-08 | Compatibility | Responsive across Android screen sizes; Material 3; dark-first with light mode. Min SDK TBD. |
| NFR-09 | Reliability | Idempotent purchase and token operations; never negative token balance; append-only ledgers; DB transactions; retries with exponential backoff. |
| NFR-10 | Observability | Structured logs, request IDs, health endpoints, failed-job monitoring, model drift monitoring. |
| NFR-11 | Compliance | AdMob/Play policy review for gambling-adjacent category; no betting promotions or affiliate links without legal approval. |
| NFR-12 | Recovery | Documented backup/restore; proposed RPO 24h, RTO 4h for self-hosted launch (needs approval). |

---

## 4. Scope boundaries

**In scope for initial release:** football; Android; 1X2, O/U goals, BTTS, correct score
(and corners only where data supports it); free + tokens + VIP + compliant ads; admin;
notifications; performance analytics.

**Out of scope:** wagering/betting; bookmaker features; iOS (future); other sports
(abstracted only); live in-play streaming; social features; chat; fantasy sports.

---

## 5. Success criteria (Phase 0 acceptance)

All 21 final acceptance criteria in the source brief remain the release gate. Phase 0
is accepted when these discovery documents are approved and the open decisions in
`00-phase0-executive-summary.md` §0.5 are resolved.
