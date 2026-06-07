# Branching guide — OrchestraOS

Three contributors, one repo, no stepping on each other's work.

| Member | Tool | Branch | Owns |
|--------|------|--------|------|
| Niket | Cursor | `niket/backbone` | Collector, detectors, breaker, Arize/partners |
| Rutuja | Antigravity | `rutuja/monitor` | Monitor model, remediation, Gemini, docs |
| Ayush | Antigravity | `ayush/dashboard` | Dashboard, Cloud Run, infra, harness |

**Repo:** https://github.com/N-i-k-e-t/orchestraos  
**GCP project:** `slimy-497412`

---

## How branching works

Think of it like three people editing copies, then merging safely.

- **`main`** — final, always-working version (protected; nobody pushes directly)
- **`dev`** — shared integration branch where everyone's work combines
- **Your branch** — personal workspace off `dev`

```
main              ← demo-ready (protected)
  └── dev         ← shared integration
        ├── niket/backbone
        ├── rutuja/monitor
        └── ayush/dashboard
```

You work on your branch → push → open a Pull Request into **`dev`**. When `dev` is stable, merge **`dev` → `main`**.

---

## Ready-made branches (already on GitHub)

These branches exist on the remote. Each person checks out their own — no need to create from scratch.

| Branch | Who |
|--------|-----|
| `niket/backbone` | Niket |
| `rutuja/monitor` | Rutuja |
| `ayush/dashboard` | Ayush |

---

## One-time setup per person

### Rutuja (Antigravity)

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git
cd orchestraos
git checkout rutuja/monitor
poetry install
cd dashboard
npm install
cd ..
copy .env.example .env
gcloud auth login
gcloud auth application-default login
gcloud config set project slimy-497412
poetry run pytest tests/ -v
```

### Ayush (Antigravity)

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git
cd orchestraos
git checkout ayush/dashboard
poetry install
cd dashboard
npm install
cd ..
copy .env.example .env
gcloud auth login
gcloud auth application-default login
gcloud config set project slimy-497412
poetry run pytest tests/ -v
```

### Niket (Cursor — already cloned)

```powershell
cd c:\Users\niket\Downloads\os-rapid
git fetch origin
git checkout niket/backbone
poetry install
copy .env.example .env
.\scripts\verify_local.ps1
```

PowerShell uses **`;`** not **`&&`** to chain commands on Windows.

---

## Daily workflow (everyone)

```powershell
# 1. Get latest shared work
git checkout dev
git pull origin dev

# 2. Bring updates into your branch
git checkout niket/backbone    # or rutuja/monitor / ayush/dashboard
git merge dev

# 3. Work, save, push
git add .
git commit -m "feat: short description"
git push

# 4. On GitHub: open Pull Request → base: dev
```

---

## Quick reference

| Action | Command |
|--------|---------|
| Start your day | `git checkout dev ; git pull origin dev` |
| Switch to your branch | `git checkout niket/backbone` (or your branch) |
| Pull team updates | `git merge dev` (while on your branch) |
| Save your work | `git add . ; git commit -m "msg" ; git push` |
| Share your work | Open PR into **`dev`** on GitHub |

---

## Protect `main` (GitHub settings)

**Private repo on Free plan:** rules show **Not enforced** — you must make the repo **public** first. Full steps: [GITHUB_SETUP.md](GITHUB_SETUP.md)

Repo → **Settings → Branches → Add classic branch protection rule** on `main`:

- Require a pull request before merging
- Required approvals: **1**

After going public, confirm the rule says **Enforced**, not “Not enforced”.

---

## Before every PR

```powershell
poetry run pytest tests/ -v
poetry run orchestraos-demo
cd dashboard ; npm run build ; cd ..
```

Or: `.\scripts\verify_local.ps1`

---

## Rules

1. **Never commit secrets** — `.env` is gitignored; production uses Secret Manager (`shared/config.py`).
2. **Do not change architecture** without team agreement.
3. **Reuse schemas** in `shared/schemas.py` — do not duplicate Pydantic models.
4. **Stay in your lane** unless fixing shared integration (coordinate first).

---

## Live dashboard note

Cloud Run dashboard deploy may be unreachable until Ayush redeploys. **Use local dashboard for demo work:**

```powershell
poetry run orchestraos-dashboard
```

Then open http://localhost:8080

See [GCP_SETUP.md](GCP_SETUP.md) and [DEPLOY.md](DEPLOY.md) for redeploy steps.

---

## Related docs

- [TEAM_SETUP.md](TEAM_SETUP.md) — onboarding checklist
- [CONTRIBUTING.md](../CONTRIBUTING.md) — commit style and PR rules
- [GCP_SETUP.md](GCP_SETUP.md) — secrets and deploy
