# Prediqo — Local testing guide (Phase 2)

No cloud, no Docker and no PostgreSQL are required. The backend runs against a local
SQLite file; the Flutter app is verified by GitHub Actions on every push.

---

## 1. Backend API — already running locally

A dev server is currently listening at **http://127.0.0.1:8000**.

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI (click **Try it out**) |
| `http://127.0.0.1:8000/health` | Liveness + dependency status |
| `http://127.0.0.1:8000/openapi.json` | Generated API contract |

**Dev token:** `prediqo-dev-token` (only accepted when `ENVIRONMENT=development` and
`AUTH_MODE=dev`; production always requires a real Firebase ID token).

### Try it in PowerShell

```powershell
$h = @{ Authorization = 'Bearer prediqo-dev-token' }

# Health
Invoke-RestMethod http://127.0.0.1:8000/health

# Provision / verify user
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/verify -Headers $h

# Profile
Invoke-RestMethod http://127.0.0.1:8000/api/v1/users/me -Headers $h

# Update profile
Invoke-RestMethod -Method Patch `
  -Uri http://127.0.0.1:8000/api/v1/users/me -Headers $h `
  -ContentType application/json `
  -Body '{"display_name":"Nick","theme":"light"}'

# Permissions
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/permissions -Headers $h

# Should return 403 for a normal user
Invoke-RestMethod http://127.0.0.1:8000/api/v1/admin/ping -Headers $h
```

### Phase 3 fixtures

The dev database is synchronised with a **clearly labelled sample adapter**
(`FOOTBALL_DATA_PROVIDER=sample`). Every record has `is_sample_data: true` and there
are no probabilities, statistics or corner values. To populate it:

```powershell
# The dev user has already been granted ADMIN locally
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/admin/sync/trigger -Headers $h
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/fixtures?page_size=3'
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/fixtures/trending'
```

Switching to a licensed real provider requires `FOOTBALL_DATA_PROVIDER=api-football`
and `FOOTBALL_DATA_API_KEY`. The adapter refuses to start without the key and never
falls back to sample data silently.

### Starting it yourself

```powershell
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///C:/Users/KipngetichNick/Documents/Default Project/backend/prediqo-dev.db"
$env:ENVIRONMENT="development"
$env:AUTH_MODE="dev"
$env:DEV_AUTH_TOKEN="prediqo-dev-token"

.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

To reset the local database, delete `backend/prediqo-dev.db` and re-run `alembic upgrade head`.

---

## 2. Backend automated tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m mypy app
```

Tests use a temporary SQLite database and the dev token — they never touch
`prediqo-dev.db` or any external service.

---

## 3. Flutter app

`flutter test` / `flutter analyze` are blocked on this Windows machine by an
Application Control policy that prevents native Dart executables from running.
They therefore run in GitHub Actions on every push. To test the UI locally you need
a normal Flutter SDK install outside the temp folder, then:

```powershell
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

(Android emulator maps host `127.0.0.1` to `10.0.2.2`; a physical device on the same
Wi-Fi uses your PC's LAN IP.)

---

## 4. CI as the shared gate

Every push to `main` or `develop` runs:

| Workflow | Checks |
|---|---|
| Backend CI | pytest, Ruff, mypy |
| Flutter CI | pub get, analyze, format, widget tests |
| Admin CI | Next.js production build |
| Dependabot | weekly dependency updates |

Open the Actions tab to see results:
https://github.com/Nicholas-Kipngetich/prediqo/actions
