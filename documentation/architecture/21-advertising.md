# Prediqo — Advertising (Phase 8)

Advertising infrastructure is implemented and **enabled using Google test ad units**.
The product owner explicitly chose to proceed without the policy-review gate that was
originally planned.

---

## Placements (remote-configurable)

| Key | Type | Default | Notes |
|---|---|---|---|
| `app_open` | App open | enabled | Shown on splash before navigation |
| `banner_home` | Banner | enabled | Home dashboard, above the match feed |
| `native_feed` | Native | disabled | Ready to enable |
| `interstitial_navigation` | Interstitial | disabled | Ready to enable |
| `rewarded_unlock` | Rewarded | disabled | Ready to enable |

All placements carry a `frequency_cap_per_hour` and `vip_excluded` flag.

## Backend

- Tables: `ad_placements`, `system_config` (migration 0007)
- Admin: `GET/PATCH /admin/ad-placements`, `GET/PATCH /admin/config`
- Public: `GET /config/client` returns only safe ad settings to the app
- Every admin change writes an audit log entry
- Test AdMob app ID and unit IDs are seeded; replace them with real IDs before launch

## Mobile

- `google_mobile_ads 9.2.0` with test unit IDs
- `AdBanner` widget renders only when config, consent and non-VIP checks pass
- App-open ad loads on splash before navigation
- VIP users never see ads (`vip_excluded`)
- Consent is stored locally; a saved decline is respected

## Policy notes

- No betting ads, bookmaker promotions or affiliate links are included.
- Ads are non-personalised in this build; no ad SDK data is shared with the prediction engine.
- Replace test IDs with production AdMob IDs and re-check Play/AdMob policies before
  public submission. Test units must never be shipped to real users.
