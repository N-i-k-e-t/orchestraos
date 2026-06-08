# Quick GCP verify — copy/paste for teammates

After `gcloud auth login` and `gcloud auth application-default login`, run this **one command** to confirm you are connected to the shared project and Pub/Sub is reachable.

## PowerShell / Bash (same)

```powershell
gcloud config set project orchestraos-498316
gcloud auth application-default set-quota-project orchestraos-498316
poetry run python -c "from google.cloud import pubsub_v1; c=pubsub_v1.PublisherClient(); topics=[t.name.split('/')[-1] for t in c.list_topics(request={'project':'projects/orchestraos-498316'})]; print('OK —', len(topics), 'topics'); print('Pipeline:', [t for t in topics if t in ('raw-spans','feature-vectors','breaker.events','remediation.actions')])"
```

## Pass criteria

| Check | Expected |
|-------|----------|
| Exit code | `0` |
| Topic count | `> 0` (currently **18** topics on the project) |
| Pipeline topics | At least **`raw-spans`** and **`feature-vectors`** in the list |

Example output (abbreviated):

```
OK — 18 topics
Pipeline: ['breaker.events', 'feature-vectors', 'raw-spans', 'remediation.actions']
```

## If it fails

| Error | Fix |
|-------|-----|
| `403` / permission denied | Ask Niket for `roles/pubsub.viewer` or `roles/editor` on `orchestraos-498316` |
| ADC / quota project warning | Run `gcloud auth application-default set-quota-project orchestraos-498316` |
| `Could not automatically determine credentials` | Run `gcloud auth application-default login` |
| Wrong project | `gcloud config set project orchestraos-498316` |

## Full local verify (no GCP needed)

```powershell
poetry run pytest tests/ -v
```

83 tests should pass with zero API keys.

See also: [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md) · [TEAM_SETUP.md](TEAM_SETUP.md)
