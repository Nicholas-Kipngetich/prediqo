# Prediqo — Security Threat Model (Phase 0)

**Method:** STRIDE per element + domain-specific abuse cases. **Status:** design-stage
threat model; to be revisited before release.

---

## 1. Assets

- Firebase identity tokens and user PII (email, display name, preferences).
- Entitlements (VIP status, token balances) and financial records (purchases, subscriptions).
- Prediction models, feature data and immutable prediction history.
- Provider API keys, Firebase service account, Google Play service account, JWT signing secret.
- Admin credentials and audit logs.

---

## 2. Trust boundaries

1. Android app ↔ backend (untrusted client).
2. Backend ↔ football data provider (external data, untrusted content).
3. Backend ↔ Google Play / Firebase (external authorities).
4. Admin dashboard ↔ backend (privileged but still untrusted input).
5. Backend ↔ database/Redis (internal, but reachable if perimeter breached).

**Governing rule:** the client is never trusted for identity, entitlement, purchase
success, price, or prediction output.

---

## 3. STRIDE summary

| Element | Spoofing | Tampering | Repudiation | Info disclosure | DoS | Elevation |
|---|---|---|---|---|---|---|
| Mobile app | Stolen Firebase token → verify token server-side, short expiry | Modified APK → Play Integrity (optional), no client-side entitlement logic | Local logs → no sensitive logs | Secrets in APK → none stored; provider keys server-only | API flooding → rate limits | Client sends admin flag → RBAC from DB |
| API | Token replay → Firebase verification + `auth_time` checks | Parameter tampering → Pydantic validation, ownership checks | Missing audit → audit middleware | Verbose errors → generic error envelope | Request flood → rate limits, WAF later | IDOR → check `user_id` ownership on every query |
| Database | — | SQL injection → SQLAlchemy parameterised queries | — | DB exposed publicly → private network, strong credentials | Connection exhaustion → pooling, timeouts | Over-privileged app role → least privilege, append-only grants |
| Provider data | Fake feed → HTTPS + API key | Poisoned stats → schema validation, plausibility checks | — | Key leak → env secrets | Provider flood → caching, backoff | LLM prompt injection → treat as data only |
| Purchases | Fake receipt → Play API verification | Replay → purchase token UNIQUE + idempotency keys | Purchase disputes → audit trail | — | Verify spam → 10/min limit | Client "I'm VIP" flag → ignored |
| Admin | Credential stuffing → Firebase + optional MFA | Unauthorised edits → RBAC + audit | — | Audit PII → access-controlled | — | Privileged action → role check + audit |

---

## 4. Domain-specific abuse cases

| ID | Threat | Mitigation |
|---|---|---|
| T-01 | Token double-spend via concurrent requests | `SELECT ... FOR UPDATE` on `token_accounts`, atomic debit + ledger insert in one DB transaction, unique idempotency key, CHECK balance >= 0. |
| T-02 | Purchase replay / double credit | UNIQUE on `google_play_order_id` and `purchase_token`; idempotency key; reconcile with Play on schedule. |
| T-03 | Entitlement bypass by hiding/unhiding UI | Every premium endpoint re-checks DB entitlements. VIP evaluated before token spend. |
| T-04 | Token unlock then VIP upgrade → double charge | Check VIP first; compensation/refund policy recorded in ledger. |
| T-05 | Manipulated prediction probabilities from client | Probabilities computed server-side from model artifacts; clients only display. |
| T-06 | LLM fabrication / prompt injection via provider text | v1 deterministic explanations; if LLM added, closed fact schema + numeric post-validation + untrusted-data handling. |
| T-07 | Fabricated trending stats | Trending ranking computed from real events/configured signals; no invented numbers. |
| T-08 | Betting/gambling policy violation | No wagering features, no betting ads or affiliate links, responsible-use wording, legal review before ads. |
| T-09 | Data scraping of proprietary content | Licensed provider only; no scraping of sites forbidding it. |
| T-10 | Account deletion vs immutable records | Pseudonymise user linkage; keep non-personal prediction records and financial ledger. |
| T-11 | Admin destructive action | Confirmation + audit log + two-person rule for SUPER_ADMIN actions (future). |
| T-12 | Push notification abuse / spoofed deep links | FCM from backend only, dedupe keys, signed deep-link routes, preferences respected. |
| T-13 | Secrets in repository | `.gitignore` excludes `.env`, keys, service accounts; `.env.example` has placeholders only; secret scanning in CI. |
| T-14 | Dependency supply chain | Dependabot, `pip-audit`, `dart pub outdated`, lockfiles, minimal dependencies. |
| T-15 | Brute force on login/password reset | Firebase rate limiting + endpoint rate limits + monitoring. |

---

## 5. Security requirements checklist (release gate)

- [ ] HTTPS enforced; HSTS at edge when deployed.
- [ ] Firebase ID token verification on all protected routes.
- [ ] RBAC enforced in backend with DB as source of truth.
- [ ] Input validation with Pydantic on every endpoint.
- [ ] Rate limiting on auth, purchase and token endpoints.
- [ ] Secrets externalised; no real credentials in repo or logs.
- [ ] CORS allow-list; no wildcard with credentials.
- [ ] Append-only ledgers and audit logs.
- [ ] Idempotent purchase/token operations.
- [ ] Dependency and secret scanning in CI.
- [ ] Security testing: authorisation, input validation, purchase flow.
- [ ] Privacy policy, Terms, Data Safety declaration, account deletion.
- [ ] AdMob/Play gambling-adjacent policy review completed.
