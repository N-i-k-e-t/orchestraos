# Contributing to OrchestraOS Loop Sentinel

Thank you for helping ship the hackathon demo. This repo is built for **three parallel contributors** — one in Cursor, two in Google Antigravity — on a shared GCP project.

## Team ownership

| Member | Tool | Primary areas | Branch prefix |
|--------|------|---------------|---------------|
| Niket | Cursor | Collector, detectors, breaker, Arize/partners | `niket/*` |
| Rutuja | Antigravity | Monitor model, remediation, Gemini, docs | `rutuja/*` |
| Ayush | Antigravity | Dashboard, Cloud Run, infra, harness | `ayush/*` |

Touch files outside your lane only for shared schemas (`shared/schemas.py`), config, or urgent integration fixes — coordinate in the team channel first.

## Branching model

```
main          ← always deployable; protected
  └── dev     ← integration branch; all feature PRs target dev first
        ├── niket/backbone      ← Niket (ready-made)
        ├── rutuja/monitor      ← Rutuja (ready-made)
        └── ayush/dashboard     ← Ayush (ready-made)
```

Full guide: [docs/BRANCHING.md](docs/BRANCHING.md)

### Standard workflow

```bash
git checkout dev
git pull origin dev
git checkout rutuja/monitor   # your ready-made branch

# ... edit, test ...

git add .
git commit -m "feat: wire Gemini Flash into RiskAgent"
git push origin rutuja/monitor
```

Open a **Pull Request → `dev`**. After review and green tests, merge to `dev`. When the demo is stable, open **`dev` → `main`**.

PowerShell equivalent:

```powershell
git checkout dev
git pull origin dev
git checkout ayush/dashboard
git add .
git commit -m "feat: polish demo page layout"
git push origin ayush/dashboard
```

## Commit message style

Use conventional prefixes:

- `feat:` — new behavior
- `fix:` — bug fix
- `docs:` — documentation only
- `chore:` — tooling, deps, CI
- `test:` — tests only

Example: `feat: export breaker trips to MongoDB incidents collection`

## Before every PR

Run locally (PowerShell):

```powershell
poetry run pytest tests/ -v
poetry run orchestraos-demo
cd dashboard; npm run build; cd ..
```

Or one command:

```powershell
.\scripts\verify_local.ps1
```

## Rules (non-negotiable)

1. **Never commit secrets** — `.env` is gitignored; production uses Secret Manager via `shared/config.py`.
2. **Do not change architecture** without team agreement — six services, one Pub/Sub fabric, one live AutoGPT scenario.
3. **Reuse schemas** — add types to `shared/schemas.py`; do not duplicate Pydantic models.
4. **Light theme only** for dashboard — see README design tokens.
5. **PowerShell** — use `;` not `&&` to chain commands on Windows.

## Protected branches

`main` should require:

- Pull request before merge
- At least one approval
- Passing tests (CI when enabled)

`dev` is the daily integration branch; keep it close to green.

## Getting started

New teammates: read [docs/BRANCHING.md](docs/BRANCHING.md), [docs/TEAM_SETUP.md](docs/TEAM_SETUP.md), and [docs/GCP_SETUP.md](docs/GCP_SETUP.md).

## Questions

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Deploy: [docs/DEPLOY.md](docs/DEPLOY.md)
- Submission: [docs/SUBMISSION.md](docs/SUBMISSION.md)
