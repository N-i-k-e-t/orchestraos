# OrchestraOS — secrets & keys (PRIVATE — do not commit to GitHub)

> **Instructions for Niket:**  
> 1. Copy this file to `TEAM_SECRETS_SHARE.md` (same folder, gitignored)  
> 2. Replace every `[PASTE HERE]` with real values  
> 3. Share `TEAM_SECRETS_SHARE.md` with Rutuja + Ayush via **Slack DM / WhatsApp only**  
> 4. Never upload to GitHub, Google Drive (public), or Antigravity chat  

---

## Golden rules

1. **Never commit** `.env`, API keys, tokens, or service account JSON  
2. **GitHub repo is public** — pushed secrets are exposed forever  
3. **Cloud Run / prod** → Secret Manager only  
4. **Local dev** → each person's own `.env` (gitignored)  

---

## Shared project (not secret)

| Setting | Value |
|---------|-------|
| GCP Project ID | `orchestraos-498316` |
| Region | `us-central1` |
| GitHub | https://github.com/N-i-k-e-t/orchestraos |

---

## Where each person adds keys

| File | Location | Who |
|------|----------|-----|
| `.env` | `orchestraos/.env` (project root) | Everyone — local machine only |

```powershell
copy .env.example .env
# Edit .env — never git add .env
```

---

## Shared team secrets (Niket: fill values, share privately)

| Secret Manager ID | Put in `.env` as | Who needs it | Value |
|-------------------|------------------|--------------|-------|
| `gemini-api-key` | `GEMINI_API_KEY` | Rutuja (Gemini tests) | `[PASTE HERE]` |
| `redis-url` | `REDIS_URL` | Prod only; local use `redis://localhost:6379/0` | `[PASTE HERE]` |
| `mongodb-uri` | `MONGODB_URI` | Optional partners | `[PASTE HERE]` |
| `phoenix-endpoint` | `PHOENIX_COLLECTOR_ENDPOINT` | Arize | `[PASTE HERE]` |
| `elastic-url` | `ELASTIC_URL` | Optional | `[PASTE HERE]` |
| `elastic-api-key` | `ELASTIC_API_KEY` | Optional | `[PASTE HERE]` |
| `dynatrace-url` | `DYNATRACE_URL` | Optional | `[PASTE HERE]` |
| `dynatrace-token` | `DYNATRACE_API_TOKEN` | Optional | `[PASTE HERE]` |
| `gitlab-token` | `GITLAB_TOKEN` | Optional | `[PASTE HERE]` |
| `gitlab-project-id` | `GITLAB_PROJECT_ID` | Optional | `[PASTE HERE]` |

---

## Per-person: what to change on YOUR system

### Everyone — safe defaults (no secrets)

```env
REDIS_URL=redis://localhost:6379/0
PUBSUB_EMULATOR_HOST=localhost:8085
GOOGLE_CLOUD_PROJECT=orchestraos-local
```

Runs: `poetry run pytest` (79 pass) + `poetry run orchestraos-demo`

---

### Rutuja — your `.env` additions

Only if not using Secret Manager via gcloud:

```env
GEMINI_API_KEY=[from table above]
```

Optional when hitting real GCP:

```env
GOOGLE_CLOUD_PROJECT=orchestraos-498316
```

---

### Ayush — your `.env` additions

Local tests: defaults only.

For deploy:

```powershell
gcloud auth login
gcloud config set project orchestraos-498316
```

No deploy keys in `.env`.

---

### Niket — your `.env` additions

Same as team; add partner keys only when testing integrations.

---

## GCP IAM (Niket runs once)

```powershell
gcloud projects add-iam-policy-binding orchestraos-498316 --member="user:RUTUJA_EMAIL@gmail.com" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding orchestraos-498316 --member="user:AYUSH_EMAIL@gmail.com" --role="roles/secretmanager.secretAccessor"
```

Teammates verify:

```powershell
gcloud secrets list --project=orchestraos-498316
```

If that works, they may **skip** pasting keys into `.env`.

---

## Checklist

- [ ] `.env` created from `.env.example`
- [ ] `git status` does not show `.env`
- [ ] `gcloud auth application-default login` done
- [ ] Keys from private TEAM_SECRETS_SHARE file pasted into `.env` locally only (or Secret Manager access works)

---

*Do not commit this file. Delete after copying to `.env` if preferred.*
