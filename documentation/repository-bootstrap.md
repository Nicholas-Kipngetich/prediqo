# Prediqo — Repository bootstrap (Phase 1, authorised)

## Local status (done)

- `git init -b main` was run in `C:\Users\KipngetichNick\Documents\Default Project`.
- `.gitignore` and `.env.example` were added.
- Git user identity is **not configured yet** — commits require it (see below).

## Remaining local setup

```powershell
# 1. Set your identity (local to this repo)
git config user.name "Your Name"
git config user.email "you@example.com"

# 2. Create the long-lived branches
git branch develop
git branch release/0.1.0

# 3. First commit
git add .
git commit -m "docs(phase-0): product discovery and architecture"
```

## Branching strategy

| Branch | Purpose |
|---|---|
| `main` | Protected, releasable code only. |
| `develop` | Integration branch for completed work. |
| `feature/*` | Per-feature work, e.g. `feature/auth`. |
| `bugfix/*` | Fixes, e.g. `bugfix/token-double-spend`. |
| `release/*` | Release candidates and final verification. |

Flow: `feature/*` → PR → `develop` → PR → `release/*` → PR → `main`.
Enable branch protection on `main` once the GitHub repo exists.

## Create the GitHub repository (when ready)

```powershell
# Requires GitHub CLI (gh) authenticated
gh repo create prediqo --private --source=. --remote=origin --push
```

Or create it at https://github.com/new (name: `prediqo`, private recommended), then:

```powershell
git remote add origin https://github.com/<your-username>/prediqo.git
git push -u origin main
git push -u origin develop
```

## Repository settings to configure

- Branch protection: require PR, 1 approval, passing status checks on `main`.
- Secrets (never in code): `POSTGRES_PASSWORD`, `FIREBASE_SERVICE_ACCOUNT`,
  `FOOTBALL_DATA_API_KEY`, `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON`, `SENTRY_DSN` (optional).
- Dependabot: enabled for pip, pub, npm and GitHub Actions.
- Issue templates: bug report, feature request, task.
- Labels: `phase-0` … `phase-12`, `blocked`, `needs-decision`, `security`.

## Planned monorepo layout (created in Phase 1)

```
prediqo/
├── mobile/
├── backend/
├── ai-engine/
├── admin-dashboard/
├── infrastructure/
├── documentation/      <- already present
├── .github/workflows/
├── docker-compose.yml
├── .env.example        <- already present
├── .gitignore          <- already present
└── README.md
```
