# Secrets — local setup (safe for GitHub)

This doc has **no secret values**. For the private key sheet, Niket shares **`TEAM_SECRETS_SHARE.template.md`** (filled in) via Slack/WhatsApp — that file is **gitignored**.

---

## Rules

1. **Never commit** `.env` or API keys — repo is **public**
2. **Production** → GCP Secret Manager (`shared/config.py` loads automatically)
3. **Local dev** → each person creates their own `.env` from `.env.example`

---

## Where to add keys (everyone)

```
orchestraos/
  .env.example   ← template (in git, no secrets)
  .env           ← YOUR keys here (gitignored, never push)
```

```powershell
copy .env.example .env
# edit .env in your editor
git status   # .env must NOT appear as staged
```

---

## What goes in `.env` vs Secret Manager

| Source | When |
|--------|------|
| `.env` on your laptop | Local pytest, demo, docker compose |
| `gcloud auth application-default login` | Read secrets from GCP without copying keys |
| Secret Manager | Cloud Run production only |

Code path: `shared/config.py` → env var first, then Secret Manager if `GOOGLE_CLOUD_PROJECT` is set and no emulator.

---

## Minimum `.env` (79 tests pass — no API keys needed)

```env
REDIS_URL=redis://localhost:6379/0
PUBSUB_EMULATOR_HOST=localhost:8085
GOOGLE_CLOUD_PROJECT=orchestraos-local
```

---

## Who adds what locally

| Person | Extra `.env` keys (optional) |
|--------|------------------------------|
| **Rutuja** | `GEMINI_API_KEY=...` when testing RiskAgent without GCP |
| **Ayush** | `GOOGLE_CLOUD_PROJECT=slimy-497412` when deploying (auth via gcloud, not `.env`) |
| **Niket** | Partner keys if testing Arize/MongoDB/etc. |

Full private sheet: ask Niket for **TEAM_SECRETS_SHARE** (not on GitHub).

---

## GCP auth (each person, own machine)

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project slimy-497412
```

Niket grants: `roles/secretmanager.secretAccessor` — see [GCP_SETUP.md](GCP_SETUP.md).

---

## Related

- [GCP_SETUP.md](GCP_SETUP.md) — Secret Manager IDs
- [setup/SECRETS_SHARE.template.md](setup/SECRETS_SHARE.template.md) — copy for private sharing
- [CHECKPOINT.md](CHECKPOINT.md) — team status
