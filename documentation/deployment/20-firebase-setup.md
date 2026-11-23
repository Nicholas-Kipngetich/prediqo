# Prediqo — Firebase setup (client authentication)

The mobile app now implements email/password registration, sign-in, password reset,
Google Sign-In, sign-out and account deletion. It currently uses **placeholder**
Firebase values so CI can compile. Replace them with a real Firebase project.

---

## 1. Create the Firebase project

1. Go to https://console.firebase.google.com and create a project.
2. Add an Android app with package name **`com.prediqo.app`**.
3. Download `google-services.json`.
4. In **Authentication → Sign-in method**, enable:
   - Email/Password
   - Google
5. In **Authentication → Settings → Authorized domains**, add your web domains if
   you add web sign-in later.
6. For Google Sign-In, add your app's **SHA-1** fingerprint in Project Settings:
   - debug: `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android`
   - release: use your upload/signing keystore.

## 2. Install the config

Replace the placeholder file:

```powershell
Copy-Item <downloaded>\google-services.json mobile\android\app\google-services.json
```

Update `mobile/lib/core/firebase_options.dart` with the `apiKey`, `appId`,
`messagingSenderId`, `projectId` and `storageBucket` from that file.

> `google-services.json` is gitignored. The committed
> `mobile/android/app/google-services.example.json` is only a placeholder used by CI.

## 3. Backend configuration

Create a Firebase service account (Project Settings → Service accounts → Generate new
private key) and set:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-service-account.json
AUTH_MODE=firebase
ENVIRONMENT=production
```

Mount the JSON file read-only into the backend container. Do **not** commit it.

## 4. How authentication flows

```
User signs in (Firebase SDK)
  → Firebase ID token
  → Dio interceptor attaches "Authorization: Bearer <token>"
  → Backend verifies with Firebase Admin SDK
  → DB user + roles + entitlements
```

In development only, a static dev token is used when Firebase is unavailable, so local
tests and the demo database keep working.

## 5. Account deletion

The Profile screen signs out of Google, deletes the Firebase user, then calls
`DELETE /api/v1/users/me`. Confirmation is required. Prediction history is retained
anonymously as documented in `documentation/legal/account-deletion.md`.
