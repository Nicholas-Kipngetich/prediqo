# Prediqo — Google Play Data Safety declaration (draft)

This draft is a factual basis for the Play Console Data Safety form. The final form must
be completed by the account owner and must match the shipped app.

---

## Data collected

| Category | Collected? | Purpose | Linked to identity? | Transient? |
|---|---|---|---|---|
| Email address | Yes | Account creation, sign-in | Yes | No |
| Name / display name | Yes | Personalisation | Yes | No |
| User ID | Yes | Account and entitlements | Yes | No |
| App activity (predictions viewed, unlocks) | Yes | Service operation and history | Yes | No |
| Purchase history | Yes (Google Play order IDs) | Entitlement verification | Yes | No |
| Device / push token | Yes, if notifications enabled | Deliver notifications | Yes | No |
| IP address / logs | Yes (server logs) | Security and operations | No | Yes (~90 days) |
| Precise location | No | — | — | — |
| Contacts / SMS / photos | No | — | — | — |
| Browsing history outside app | No | — | — | — |

## Data sharing

- **Firebase** — authentication and push messaging.
- **Google Play** — purchase and subscription verification.
- **Football data provider** — supplies match data to the backend; receives no personal data.

No sale of user data. No third-party advertising SDK is active in this build; advertising
remains disabled pending policy review.

## Data deletion

Account deletion is available in-app (Profile → Settings). See `account-deletion.md`.
Prediction history and audit records are retained in pseudonymised form for integrity.

## Encryption in transit

HTTPS/TLS for all client-server communication.

## Security practices

Server-side authorisation, Firebase token verification, immutable ledgers, audit logs,
secret management via environment variables, and dependency update automation.

---

**Note:** if advertising is enabled in a future release, this declaration must be
updated before submission, including any ad-network data collection.
