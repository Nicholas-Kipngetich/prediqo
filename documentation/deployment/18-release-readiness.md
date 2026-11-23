# Prediqo — Release readiness (Phase 12)

---

## 1. Final acceptance criteria status

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Flutter app builds successfully | ✅ CI green; local Android build pending device tooling | Flutter CI |
| 2 | Android app works on real devices | ⏳ Not yet tested | Requires physical device |
| 3 | Backend operates reliably | ✅ 44 tests + live checks | test report |
| 4 | PostgreSQL migrations work | ✅ 0001–0005 applied on SQLite; Postgres to verify in staging | alembic upgrade head |
| 5 | Authentication secure | ✅ Firebase verification + RBAC tests | security review |
| 6 | Real football data integrated | ⚠️ Adapter ready; licence/budget pending | provider evaluation |
| 7 | Match analysis uses verified data | ✅ No fabricated stats; sample labelled | fixtures API |
| 8 | Probabilities from evaluated models | ✅ Poisson/Elo ensemble + metrics | AI engine tests |
| 9 | Prediction history preserved | ✅ Immutable snapshots | predictions schema |
| 10 | Settlement works | ✅ 16 settled live | settlement tests |
| 11 | Token purchases verified | ✅ Ledger + dev verification; Play sandbox pending | monetization tests |
| 12 | VIP entitlements work | ✅ VIP bypasses token charge | subscription tests |
| 13 | Ads compliant | ⏸ Deferred pending policy review | Phase 8 decision |
| 14 | Admin dashboard works | ✅ Live at :3000 | admin tests |
| 15 | Notifications work | ✅ Dedupe + prefs verified; FCM device test pending | notification tests |
| 16 | Automated tests pass | ✅ 50 tests green | test report |
| 17 | Security checks complete | ⚠️ Internal review done; pentest pending | security review |
| 18 | Deployment documentation exists | ✅ | hosting doc |
| 19 | Backup/recovery tested | ✅ Local restore verified | hosting doc |
| 20 | Privacy/legal docs ready | ⚠️ Drafts prepared; legal review + public URL needed | legal folder |
| 21 | Google Play requirements met | ⏳ Checklist below; submission not attempted | this document |

---

## 2. Google Play preparation checklist

**App bundle & assets**
- [ ] Generate signed Android App Bundle (`flutter build appbundle --release`)
- [ ] Upload signing keystore to a secure location (never commit)
- [ ] App icon (original artwork)
- [ ] Feature graphic
- [ ] Screenshots from a real device
- [ ] Short and full descriptions
- [ ] Verify current target API level before upload

**Policies & legal**
- [ ] Publish Privacy Policy at a public HTTPS URL
- [ ] Publish Terms at a public HTTPS URL
- [ ] Publish Account Deletion URL
- [ ] Complete Data Safety form matching `data-safety.md`
- [ ] Content rating questionnaire
- [ ] Target audience declaration
- [ ] Advertising declaration (ads currently disabled)
- [ ] Confirm no gambling promotion or betting affiliate links

**Technical**
- [ ] Test on at least two real Android devices / API levels
- [ ] Remove dev token mode from release build (enforced by env)
- [ ] Confirm `ALLOW_SAMPLE_DATA=false`
- [ ] Verify Google Play Billing sandbox purchases and subscriptions
- [ ] Verify FCM on a real device
- [ ] Review permissions; remove unused ones
- [ ] Confirm no secrets in APK or repository

---

## 3. Release process

1. Merge `develop` → `main` via pull request after all CI checks pass.
2. Tag `vX.Y.Z` (`git tag -a v0.1.0 -m "First release candidate"`).
3. Build backend/admin/prod images and run migrations in staging.
4. Run full test report and backup verification.
5. Build signed app bundle and upload to Play Console internal track.
6. Run internal + closed testing; collect crash/analytics feedback.
7. Complete policy declarations and submit for review.
8. Do **not** promise approval before Google Play reviews the app.

---

## 4. Deferred / blocked items

| Item | Blocker |
|---|---|
| Real data | Licensed provider + monthly budget approval |
| Advertising | Legal/policy review of gambling-adjacent category |
| Play purchase verification | Service account + sandbox testing |
| FCM delivery | Firebase project + registered device |
| Independent pentest | Budget/scheduling |

---

## 5. Go/no-go summary

**Technical go:** the backend, admin dashboard, statistical engine and CI are in a
verified state.

**Conditional items before public release:** real device testing, legal review/public
policy URLs, provider licence, Play sandbox verification, and load testing. The app is
**not** ready for public submission until those are closed.
