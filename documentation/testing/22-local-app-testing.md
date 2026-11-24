# Prediqo — How to test the app now

Three ways to test, from quickest to most realistic.

---

## 1. API (already running)

- Swagger UI: **http://127.0.0.1:8000/docs**
- LAN URL: **http://192.168.1.67:8000/docs**
- Dev token: `prediqo-dev-token`

Click **Authorize** and paste `Bearer prediqo-dev-token`, then try:
`GET /api/v1/fixtures`, `GET /api/v1/predictions?market=1X2`,
`GET /api/v1/performance/overview`, `GET /api/v1/config/client`.

## 2. Admin dashboard (already running)

Open **http://localhost:3000**. Pages: Overview, Users, Predictions (with
sync/generate/settle buttons), Monetization, System (health + audit log).

It calls the same backend with the dev token.

## 3. Android app

A release APK is built by the `Flutter Release Build` workflow. Download the
`prediqo-apk` artifact from the Actions run, extract it, then:

```powershell
adb install builds\apk\app-release.apk
```

Or copy `app-release.apk` to the phone and tap it (enable "Install unknown apps").

The local test APK is built with:
- `API_BASE_URL=http://192.168.1.67:8000`
- `DEV_BYPASS_AUTH=true` (skips Firebase sign-in, uses the dev token)

Requirements:
- Phone on the same Wi-Fi network
- Windows firewall allowing inbound TCP 8000
- Backend started with `--host 0.0.0.0`

### What to test in the app
1. Splash → Home (dev bypass)
2. Home: fixtures, trending, token balance, demo banner ad
2. Search: tap the search icon on Home, try "Sample"
3. Matches: filter chips (Upcoming / Results / Trending) and expandable competition sections
4. Match detail → analysis: first fixture opens, second is blocked by the daily quota
5. Predictions: History button shows settled predictions with outcomes
6. Profile → Settings: theme, notifications, favourites
5. Predictions feed with probability bars
6. Performance centre with accuracy and sample size
7. Profile → Token Store / VIP / Notifications

Note: real Firebase sign-in requires replacing the placeholder `google-services.json`;
see `documentation/deployment/20-firebase-setup.md`.
