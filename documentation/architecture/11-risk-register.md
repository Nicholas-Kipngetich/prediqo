# Prediqo — Technical Risk Register (Phase 0)

**Legend:** Likelihood/Impact = Low / Medium / High. Status = Open / Mitigated / Accepted.

| ID | Risk | L | I | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | No licensed data provider approved → no real data | High | High | Obtain budget decision in Phase 0; evaluate API-Football/football-data.org; provider abstraction ready | Product owner | **Open — blocker** |
| R-02 | Provider ToS forbids redistribution or ML training | Medium | High | Confirm commercial licence in writing; avoid scraping; use StatsBomb open data for R&D | Architect | Open |
| R-03 | Play/AdMob rejects prediction app as gambling-adjacent | Medium | High | No betting content; legal review; ads off by default; compliant wording | Product + Legal | Open |
| R-04 | Model performs poorly or is uncalibrated | Medium | High | Chronological validation, walk-forward, Brier/log-loss gates, suppression rules, champion/challenger | ML lead | Open |
| R-05 | Data leakage inflates backtest results | Medium | High | As-of feature builder, leakage tests, immutable feature snapshots | ML lead | Open |
| R-06 | Recommended free limits/prices never decided | High | Medium | Phase 0 decision checklist; defaults in `.env.example` as placeholders only | Product owner | Open |
| R-07 | Purchase verification bug credits tokens twice | Low | High | Idempotency keys, UNIQUE purchase tokens, row locks, ledger tests, scheduled reconciliation | Backend lead | Mitigated by design |
| R-08 | Entitlement bypass through client manipulation | Medium | High | Backend enforcement on every premium endpoint; no client trust | Backend lead | Mitigated by design |
| R-09 | Negative token balance under concurrency | Low | High | Atomic transaction + FOR UPDATE + CHECK constraint + concurrency tests | Backend lead | Mitigated by design |
| R-10 | Provider downtime / rate-limit exhaustion | Medium | Medium | Redis cache, stale-while-revalidate, backoff, job monitoring, provider fallback | Backend lead | Open |
| R-11 | Timezone/kickoff display errors | Medium | Medium | UTC storage, IANA timezone IDs, client conversion, tests across zones | Mobile lead | Open |
| R-12 | Android device fragmentation / performance | Medium | Medium | Material 3 responsive layouts, minSdk decision, device testing, image optimisation | Mobile lead | Open |
| R-13 | Secrets leaked in repo or APK | Low | High | `.gitignore`, `.env.example`, secret scanning, no provider keys in app | DevOps | Mitigated by design |
| R-14 | Account deletion conflicts with immutable history | Medium | Medium | Pseudonymisation policy, legal review, documented retention | Backend + Legal | Open |
| R-15 | Scope explosion / unrealistic timeline | High | Medium | Strict phase gates, documented roadmap, tracker statuses, no big-bang build | PM | Open |
| R-16 | Flutter/Docker not installed → Phase 1 delay | High | Low | Tooling checklist in bootstrap doc; verify Flutter/Docker versions early | Developer | Open |
| R-17 | Prediction language interpreted as betting advice | Medium | High | Informational wording, no "sure win", responsible-use notice, policy review | Product + Legal | Open |
| R-18 | Admin insider abuse | Low | High | RBAC, audit logs, least privilege, future two-person rule | Backend lead | Open |
| R-19 | Ad revenue assumptions invalid | Medium | Medium | Do not budget on ad revenue; token/VIP primary; ads optional | Product owner | Accepted |
| R-20 | Backup/restore never tested | Medium | High | Backup scripts + scheduled restore drill before release (Phase 12) | DevOps | Open |

---

## Tracker status vocabulary (per brief)

Every task must be one of: **Not started · In progress · Blocked · Implemented · Tested · Accepted**.

Phase 0 tasks status example:
- Product discovery — Accepted (this document set, pending sign-off)
- Data provider decision — Blocked (awaiting budget)
- Free-limit/pricing decision — Blocked (awaiting product owner)
- Repository bootstrap — Implemented (local git init done; GitHub remote pending)
