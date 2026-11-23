# Prediqo — Account deletion (Google Play requirement)

Google Play requires apps that support account creation to provide an in-app deletion
path and a public web URL describing the process.

---

## In-app path

**Profile → Settings → Delete account**

Current implementation:
- `DELETE /api/v1/users/me` performs a soft deletion.
- `users.status` becomes `DELETED`, `deleted_at` is set, and email/display name are
  cleared.
- The Firebase account must also be deleted by the client; the backend endpoint alone
  does not delete the Firebase identity. The mobile client should call
  `FirebaseAuth.currentUser.delete()` before/with the API call, and re-authenticate the
  user if required by Firebase.

## What is deleted or pseudonymised

| Data | Action |
|---|---|
| Email, display name | Cleared immediately |
| Profile preferences | Cleared with account |
| Device tokens | Removed |
| Notification history | Removed |
| Token balance and ledger | Retained in pseudonymised form for financial integrity |
| Prediction records | Retained as non-personal analytics, no longer linked to the account |
| Audit logs | Retained in pseudonymised form for security/legal purposes |

## Public web URL (required for Play)

Publish this document at a stable HTTPS URL (for example
`https://prediqo.app/account-deletion`) and include it in the Google Play listing and
the app's Terms.

## Remaining work before release

1. Add the client-side Firebase account deletion call in the Profile screen.
2. Add a confirmation dialog explaining what is retained.
3. Publish the public web page.
