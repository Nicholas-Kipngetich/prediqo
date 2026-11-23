# Prediqo — API Specification (Phase 0)

**Base path:** `/api/v1` · **Protocol:** HTTPS only · **Format:** JSON · **Docs:** FastAPI OpenAPI/Swagger at `/docs`.

---

## 1. Conventions

### Pagination
Request: `?page=1&page_size=20` (max 100). Response:
```json
{ "items": [], "page": 1, "page_size": 20, "total": 137 }
```

### Error envelope
```json
{
  "error": {
    "code": "ENTITLEMENT_REQUIRED",
    "message": "An active VIP subscription or tokens are required.",
    "details": { "required": "FULL_REPORT", "balance": 2 },
    "request_id": "9f1c..."
  }
}
```
Standard codes: `VALIDATION_ERROR` (422), `UNAUTHORIZED` (401), `FORBIDDEN` (403),
`NOT_FOUND` (404), `CONFLICT` (409), `RATE_LIMITED` (429), `UPSTREAM_ERROR` (502),
`INSUFFICIENT_DATA` (422), `ENTITLEMENT_REQUIRED` (403).

### Authentication
`Authorization: Bearer <Firebase ID token>`. Backend verifies via Firebase Admin SDK,
loads the user from DB, and resolves entitlements. Protected endpoints require a valid
token; public endpoints (fixtures, trending, selected predictions) may allow guests.

### Idempotency & rate limits
`Idempotency-Key` header required on `POST /tokens/purchases/verify`,
`POST /tokens/spend`, `POST /subscriptions/verify`. Rate limits per role:
guest 60 req/min, free 120, VIP 300, admin 600; stricter limits on auth and purchase
endpoints (5/min). Return `429` with `Retry-After`.

### Entitlement header/response
All premium responses include `X-Prediqo-Entitlement: vip | token | free`.

---

## 2. Public & user endpoints

| Method | Path | Purpose | Auth | Response | Limits |
|---|---|---|---|---|---|
| GET | `/health` | Liveness/readiness | None | `{status, version, db, redis}` | 60/min |
| GET | `/fixtures` | Browse fixtures; filters: `date_from`,`date_to`,`status`,`country`,`competition_id`,`team_id`,`page`,`page_size` | Optional | `FixturePage` | 120/min |
| GET | `/fixtures/{id}` | Fixture detail | Optional | `FixtureDetail` | 120/min |
| GET | `/fixtures/{id}/analysis` | Full analysis; premium sections gated | Optional | `MatchAnalysis` | 60/min |
| GET | `/fixtures/{id}/analysis/premium` | Full report | Required + entitlement | `PremiumReport` | 30/min |
| GET | `/fixtures/trending` | Trending fixtures | Optional | `FixturePage` | 120/min |
| GET | `/competitions` | List competitions | Optional | `CompetitionPage` | 120/min |
| GET | `/teams/{id}/form` | Team form snapshot | Optional | `TeamForm` | 120/min |
| GET | `/teams/{id}/head-to-head?opponent_id=` | H2H | Optional | `HeadToHead` | 120/min |
| GET | `/predictions` | Feed; filters `market`,`date`,`competition_id`,`status` | Optional | `PredictionPage` | 120/min |
| GET | `/predictions/history` | User's history (auth) / public sample | Optional | `PredictionPage` | 120/min |
| GET | `/predictions/{id}` | Prediction detail + explanation | Optional | `PredictionDetail` | 120/min |
| GET | `/performance/overview` | Aggregates with sample sizes | Optional | `PerformanceOverview` | 60/min |
| GET | `/performance/breakdown?by=market\|competition\|week\|month` | Breakdowns | Optional | `Breakdown[]` | 60/min |
| GET | `/performance/calibration` | Calibration curve data | Optional | `Calibration` | 60/min |
| GET | `/users/me` | Profile | Required | `UserProfile` | 120/min |
| PATCH | `/users/me` | Update profile/preferences | Required | `UserProfile` | 60/min |
| PUT | `/users/me/favorites/teams` | Set favourite teams | Required | `UserProfile` | 60/min |
| PUT | `/users/me/favorites/competitions` | Set favourite competitions | Required | `UserProfile` | 60/min |
| DELETE | `/users/me` | Account deletion request | Required | `202 Accepted` | 5/min |
| GET | `/tokens/balance` | Balance + recent transactions | Required | `TokenBalance` | 120/min |
| GET | `/tokens/packages` | Available packages | Optional | `TokenPackage[]` | 120/min |
| GET | `/tokens/transactions` | Transaction history | Required | `TransactionPage` | 120/min |
| POST | `/tokens/purchases/verify` | Verify Play purchase, credit tokens | Required | `PurchaseResult` | 10/min |
| POST | `/tokens/spend` | Unlock report with tokens | Required | `UnlockResult` | 30/min |
| GET | `/tokens/unlocks` | Unlocked reports | Required | `UnlockPage` | 120/min |
| GET | `/subscriptions/plans` | Plans | Optional | `Plan[]` | 120/min |
| GET | `/subscriptions/status` | Current subscription + entitlements | Required | `SubscriptionStatus` | 120/min |
| POST | `/subscriptions/verify` | Verify/restore subscription | Required | `SubscriptionStatus` | 10/min |
| POST | `/subscriptions/manage` | Return Play manage URL | Required | `{url}` | 10/min |
| GET | `/notifications` | List notifications | Required | `NotificationPage` | 120/min |
| PATCH | `/notifications/preferences` | Update preferences | Required | `Preferences` | 60/min |
| POST | `/notifications/{id}/read` | Mark read | Required | `Notification` | 120/min |
| GET | `/config/client` | Safe client config, limits, ad placements, feature flags | Optional | `ClientConfig` | 120/min |

---

## 3. Admin endpoints

All require `ADMIN` or `SUPER_ADMIN` and write an audit log entry.

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/dashboard` | KPIs: users, active, VIP, purchases, jobs, model health |
| GET/PATCH | `/admin/users` | Search, inspect, suspend, adjust entitlements |
| GET/POST/PATCH | `/admin/competitions`, `/admin/teams`, `/admin/fixtures` | Sports management |
| POST | `/admin/sync/trigger` | Trigger provider synchronisation |
| GET | `/admin/sync/jobs` | Job status and failures |
| GET/POST | `/admin/predictions` | List, publish, suppress |
| POST | `/admin/predictions/{id}/settle` | Manual settlement |
| POST | `/admin/predictions/{id}/correct` | Append-only correction (reason required) |
| GET/POST/PATCH | `/admin/model-versions`, `/admin/model-evaluations` | Model registry |
| GET/POST/PATCH | `/admin/token-packages`, `/admin/subscription-plans` | Monetisation config |
| GET/POST | `/admin/refunds` | Refund events → compensating ledger entries |
| GET | `/admin/system/health` | API, DB, Redis, provider status |
| GET | `/admin/audit-logs` | Query audit trail |
| GET/PATCH | `/admin/config`, `/admin/ad-placements` | Config & ad frequency controls |

---

## 4. Representative schemas

```jsonc
// Fixture (abridged)
{
  "id": "uuid",
  "competition": {"id": "uuid", "name": "Premier League", "country": "England"},
  "season": {"id": "uuid", "label": "2026/27"},
  "home_team": {"id": "uuid", "name": "Team A", "logo_url": null},
  "away_team": {"id": "uuid", "name": "Team B", "logo_url": null},
  "kickoff_utc": "2026-11-24T20:00:00Z",
  "kickoff_local": "2026-11-24T23:00:00+03:00",
  "status": "SCHEDULED",
  "venue": "Stadium Name",
  "score": null,
  "probabilities": {"1X2": {"home": 4520, "draw": 2780, "away": 2700}}, // basis points
  "analysis_available": true,
  "is_premium": true
}
```

```jsonc
// MatchAnalysis (abridged)
{
  "fixture_id": "uuid",
  "data_as_of": "2026-11-23T06:00:00Z",
  "provider": "api-football",
  "markets": {
    "1X2": {"home": 4520, "draw": 2780, "away": 2700},
    "over_under": {"2.5": {"over": 5310, "under": 4690}},
    "btts": {"yes": 4820, "no": 5180},
    "correct_score": {"1-0": 1180, "1-1": 1020, "...": 0}
  },
  "goals": {"expected_home": 1.61, "expected_away": 1.24, "total": 2.85},
  "corners": null,              // null = insufficient verified data
  "team_form": {"home": {...}, "away": {...}},
  "head_to_head": {"matches": 12, "...": {}},
  "advanced": {"rest_days": {"home": 5, "away": 8}, "lineups": null},
  "explanation": {
    "type": "deterministic_v1",
    "facts_used": [" elo_diff ", "home_form_xg", "poisson_lambda"],
    "text": "Home are favoured because ..."
  },
  "premium": {"full_report": {"entitlement": "token_or_vip", "cost_tokens": 5}}
}
```

```jsonc
// TokenTransaction
{
  "id": "uuid", "type": "DEBIT", "amount": -5, "balance_after": 12,
  "reason": "UNLOCK_FULL_REPORT", "reference_type": "prediction",
  "reference_id": "uuid", "created_at": "2026-11-23T10:12:00Z"
}
```

---

## 5. Non-functional API requirements

- OpenAPI generated automatically from Pydantic models; schemas are the contract.
- Pydantic validation on all inputs; SQLAlchemy parameterised queries (no string SQL).
- CORS allow-list from `CORS_ORIGINS`; credentials allowed only for known origins.
- Request ID middleware; structured logs with user id (hashed), route, latency, status.
- Client cache headers (`Cache-Control`, `ETag`) on fixture/analysis endpoints;
  server Redis cache with 60–300 s TTL, stale-while-revalidate on provider failure.
- All premium reads re-check entitlement server-side; no client-supplied entitlement flags.
- Payment verification endpoints are idempotent and reconcile with Play on a schedule.
