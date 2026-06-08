# GitHub setup — public repo + branch protection

OrchestraOS uses a **public** GitHub repo so branch protection works on the **free** plan. Only **collaborators** can push or merge; the public can read/clone only.

---

## Why public?

| Repo visibility | Branch protection on Free plan |
|-----------------|-------------------------------|
| **Private** | Created but **Not enforced** (needs GitHub Team — paid) |
| **Public** | **Enforced** — PR + approval required on `main` |

Your screenshot showed `main` → **Not enforced** because the repo was private. Making it public fixes that without paying for Team.

---

## What “public” actually means (security)

```
┌─────────────────────────────────────────────────────────────┐
│  Anyone on the internet                                     │
│  ✓ Can VIEW code (read)                                     │
│  ✓ Can FORK and clone                                       │
│  ✗ Cannot PUSH to your branches                             │
│  ✗ Cannot MERGE without your approval (if protection on)    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Collaborators only (you, Rutuja, Ayush)                    │
│  ✓ Can push to dev and personal branches                    │
│  ✓ Can open and merge PRs (with review rules)               │
│  ✗ Cannot push directly to main (branch protection)         │
└─────────────────────────────────────────────────────────────┘
```

**Public ≠ anyone can change your code.** Write access is still invite-only via **Settings → Collaborators**.

---

## Step 1 — Make the repo public

1. Open https://github.com/N-i-k-e-t/orchestraos  
2. **Settings** (top bar)  
3. Scroll to **Danger Zone** (bottom of General settings)  
4. Click **Change repository visibility**  
5. Select **Make public**  
6. Type the repo name `N-i-k-e-t/orchestraos` to confirm  
7. Click **I understand, make this repository public**

Wait ~30 seconds, then refresh **Settings → Branches**.

Your existing `main` rule should change from **Not enforced** → **Enforced** (green).

If it still says Not enforced, click **Edit** on the rule and **Save** again.

---

## Step 2 — Confirm branch protection on `main`

**Settings → Branches → Branch protection rules → Edit** (on `main`)

Required settings:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require a pull request before merging | **On** |
| Required approvals | **1** |
| Allow force pushes | **Off** |
| Allow deletions | **Off** |

Click **Save changes**.

---

## Step 3 — Lock down collaborators (only your team)

**Settings → Collaborators** (or **Manage access**)

| Person | Role | Why |
|--------|------|-----|
| Niket (you) | Admin | Owns repo |
| Rutuja | Write | Can push branches + open PRs |
| Ayush | Write | Can push branches + open PRs |

**Do not** add random accounts. **Do not** give Write to strangers.

Optional: **Settings → General → Features** — you can leave **Allow forking** on (harmless; forks are separate copies).

---

## Step 4 — Secrets safety (critical for public repo)

Because code is public, **never commit**:

| Never in git | Use instead |
|--------------|-------------|
| `.env` with real keys | `.env` local only (gitignored) |
| API keys, MongoDB URI | GCP Secret Manager |
| `service-account.json` | `gcloud auth` locally; SA in GCP only |
| GCP project keys in README | Reference project ID only (`orchestraos-498316`) |

Before making public, confirm:

```powershell
# From repo root — should show nothing sensitive staged
git status
git check-ignore -v .env
```

`.env` must appear as ignored. Real keys live in Secret Manager — see [GCP_SETUP.md](GCP_SETUP.md).

---

## Step 5 — Verify protection works

### Test A — direct push to `main` should fail

```powershell
cd c:\Users\niket\Downloads\os-rapid
git checkout main
git pull origin main
echo "# test" >> README.md
git add README.md
git commit -m "test: should be blocked"
git push origin main
```

**Expected:** GitHub rejects the push (protected branch).

Undo locally if the push failed:

```powershell
git reset --hard HEAD~1
git checkout niket/backbone
```

### Test B — PR workflow should work

1. Push a small change on `niket/backbone`  
2. Open PR → base **`dev`** on GitHub  
3. Rutuja or Ayush approves  
4. Merge

For `main`: only merge **`dev` → `main`** via PR after demo is stable.

---

## Hackathon note

Many hackathons require a **public repo** for submission anyway. Public + collaborators-only write is the standard setup for student/team projects.

---

## If you must stay private

Only options:

1. **Pay** for GitHub Team (org account) — branch rules enforced on private repos  
2. **Trust-based workflow** — no enforced protection; team agrees never to push to `main` directly  

For a free hackathon team, **public repo is the right choice**.

---

## Quick checklist

- [ ] Repo visibility → **Public**
- [ ] `main` branch rule → **Enforced** (not “Not enforced”)
- [ ] Require PR + **1 approval** on `main`
- [ ] Only **3 collaborators** with Write/Admin
- [ ] No secrets in git (`.env` gitignored, Secret Manager for prod)
- [ ] Team uses PRs into **`dev`**, not direct pushes to **`main`**

Related: [BRANCHING.md](BRANCHING.md) · [TEAM_SETUP.md](TEAM_SETUP.md) · [GCP_SETUP.md](GCP_SETUP.md)
