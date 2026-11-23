# Prediqo — Test report (Phase 12)

Date: 2026-11-23
Scope: all automated suites and live integration checks completed to date.

---

## 1. Automated results

| Suite | Command | Result |
|---|---|---|
| Backend unit + API tests | `pytest -q` (backend) | **47 passed** (includes 3 Celery automation tests) |
| AI-engine tests | `pytest -q ../ai-engine/tests` | **6 passed** |
| Backend lint | `ruff check app tests` | clean |
| Backend format | `ruff format --check app tests` | 65 files formatted |
| Backend types | `mypy app` | no issues in 53 files |
| Flutter CI | `flutter analyze`, strict `dart format`, `flutter test` | green on `main` and `develop` |
| Admin CI | `npm ci && npm run build` | 6 routes compiled |
| Android release | `flutter build appbundle --release` (tag/dispatch workflow) | ✅ AAB produced (52.4 MB artifact with Firebase auth plugins) |
| Backend CI | tests + lint + format + types + AI tests | green |

Total automated tests: **53 passing** (47 backend + 6 AI-engine), plus 1 Flutter widget
test and 6 compiled admin routes.

Background automation is registered with Celery Beat: fixture sync every 6 hours,
prediction generation hourly, settlement every 30 minutes and notification generation
every 15 minutes.

---

## 2. Live integration checks performed

| Area | Result |
|---|---|
| Auth + RBAC | dev token provisioned user; admin endpoint returned 403 for normal user, 200 for admin |
| Fixtures | sync produced 3 competitions, 8 teams, 28 labelled sample fixtures |
| Matching | 1X2 feed returned 7 records, probabilities summed to 10,000 |
| Settlement | 16 predictions settled; overview reported accuracy 0.5 with sample size 16 |
| Purchases | 5 tokens credited once; duplicate purchase returned `already_credited` |
| VIP | subscription verified, `VIP_USER` granted, VIP unlock skipped token charge |
| Notifications | preferences returned; test notification deduped; 2 reminders generated without duplicates |
| Admin dashboard | rendered live data: 1 user, 28 predictions, 1 sync job, DB healthy |
| Backup/restore | SQLite backup restored preserving 1 user, 28 predictions, 3 notifications |

---

## 3. Not yet verified

| Item | Reason | Required before release |
|---|---|---|
| Physical Android device | Flutter runtime blocked by local Application Control policy | Run on a real device |
| Load / stress test | No production-like environment provisioned | Execute against VPS/PaaS |
| Real provider data | No licensed provider approved | Confirm licence and budget |
| Google Play purchase verification | Requires Play service account + real purchase | Sandbox test |
| FCM delivery | Requires Firebase project + device token | Integration test |
| AdMob policy compliance | Legal review pending | Do not enable ads |

---

## 4. Test philosophy applied

- No feature is marked complete without a test or verifiable check.
- Losing predictions are never deleted and accuracy always reports sample size.
- Sample data is always labelled `DEMO`; production suppresses it via
  `ALLOW_SAMPLE_DATA=false`.
- Backend enforces every entitlement; UI hiding is never used as authorisation.
