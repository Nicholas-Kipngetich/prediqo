# Prediqo — Security Review (Phase 12)

**Status:** design + implementation review completed. This is a pre-release assessment,
not a certification.

---

## 1. Controls implemented

| Area | Control | Evidence |
|---|---|---|
| Transport | HTTPS required in production; reverse proxy terminates TLS | `documentation/deployment/16-hosting.md` |
| Identity | Firebase ID token verified server-side on every protected route | `app/core/auth.py`, `app/api/deps.py` |
| Authorisation | DB-backed RBAC; `USER`/`VIP_USER`/`ADMIN`/`SUPER_ADMIN`; backend checks on every admin/premium endpoint | `app/api/deps.py`, `app/api/v1/endpoints/admin.py` |
| Entitlements | VIP derived from server-verified subscription; never from client flag | `app/services/subscription_service.py` |
| Tokens | Immutable ledger, CHECK balance >= 0, unique idempotency keys, row lock on account | `app/models/monetization.py`, `app/services/token_service.py` |
| Purchases | Google Play Developer API verification with service account; dev verifier disabled outside development | `app/services/billing_service.py` |
| Predictions | Immutable snapshots; corrections append-only; no deletion of losing records | `app/models/predictions.py` |
| Data provider | Server-side API key; provider abstraction; no client-side keys | `app/providers/` |
| Secrets | `.gitignore` excludes `.env`, keys, service accounts; `.env.example` placeholders only | `.gitignore`, `.env.example` |
| Audit | Admin sync and sensitive actions written to `audit_logs` | `app/services/audit_service.py` |
| Input validation | Pydantic models on all request bodies/query params | `app/schemas/` |
| Errors | Generic error envelope; no stack traces to client | `app/core/errors.py` |
| Notifications | Deduplicated by unique key; preferences enforced | `app/services/notification_service.py` |

---

## 2. STRIDE summary (current state)

| Threat | Mitigation | Residual risk |
|---|---|---|
| Spoofing identity | Firebase token verification | Low; depends on Firebase project config |
| Tampering with purchase result | Server-side Play verification, unique purchase token | Low; Play service account must be configured |
| Repudiation of admin actions | Audit log with actor and timestamp | Low |
| Information disclosure | No secrets in repo/APK, least-privilege DB role recommended | Medium — production DB role grants must be reviewed at deploy time |
| Denial of service | Rate limits configured in API spec; caching | Medium — needs load test and edge protection |
| Elevation of privilege | DB roles, not client flags | Low |
| LLM fabrication | No LLM in numeric path; deterministic explanations | Low |
| Betting/gambling policy | No wagering features; ads deferred | Medium — legal review still required |

---

## 3. Outstanding actions before public release

1. **Rotate all development secrets** and generate production `SECRET_KEY`, Firebase service account, Play service account, provider API key.
2. **Review DB grants** so the application role cannot UPDATE/DELETE `token_transactions`, `predictions`, `audit_logs`, `prediction_settlements`.
3. **Enable GitHub secret scanning and Dependabot** on the repository (Dependabot already configured).
4. **Load test** against production-like infrastructure; current targets are planning assumptions only.
5. **AdMob/Play policy review** before enabling any ads; keep `ADMOB_ENABLED=false` until approved.
6. **Privacy policy and Terms** must be published at a public HTTPS URL and linked in the app/Play listing.
7. **Google Play Data Safety declaration** must match actual data collection (see `documentation/legal/data-safety.md`).

---

## 4. Known limitations

- The dev static token (`prediqo-dev-token`) is accepted only when
  `ENVIRONMENT=development` **and** `AUTH_MODE=dev`. Production compose sets
  `AUTH_MODE=firebase` and `ALLOW_SAMPLE_DATA=false`.
- FCM delivery in dev is simulated; real delivery requires a Firebase project and
  registered device tokens.
- The app has not yet been penetration-tested by an independent third party.
