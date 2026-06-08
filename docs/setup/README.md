# Teammate setup — start here

Pick your guide:

| Who | Easy guide | Antigravity prompt (paste in IDE) |
|-----|------------|-----------------------------------|
| **Rutuja** | [RUTUJA_SETUP.md](RUTUJA_SETUP.md) | [ANTIGRAVITY_PROMPT_RUTUJA.md](ANTIGRAVITY_PROMPT_RUTUJA.md) |
| **Ayush** | [AYUSH_SETUP.md](AYUSH_SETUP.md) | [ANTIGRAVITY_PROMPT_AYUSH.md](ANTIGRAVITY_PROMPT_AYUSH.md) |
| **Niket** | Branch `niket/backbone` in Cursor | — |

**Repo:** https://github.com/N-i-k-e-t/orchestraos (public — only collaborators can push)  
**GCP project:** `orchestraos-498316`

**Project status:** [CHECKPOINT.md](../CHECKPOINT.md)

**Secrets:** [SECRETS_LOCAL.md](../SECRETS_LOCAL.md) (on GitHub, no values). Niket shares filled [SECRETS_SHARE.template.md](SECRETS_SHARE.template.md) via **Slack/WhatsApp only**.

**Live resources:** [LIVE_RESOURCES.md](../LIVE_RESOURCES.md) — keys, auth, GCP config, test scenarios.

**Cloud Shell SA (done):** [CLOUD_SHELL_SETUP.md](../CLOUD_SHELL_SETUP.md) — `orchestraos-sa` on `orchestraos-498316`.

**Verify GCP (30 sec):** [VERIFY_GCP.md](../VERIFY_GCP.md) — one command to list Pub/Sub topics.

**What's left + GCP deploy:** [REMAINING_WORK.md](../REMAINING_WORK.md) — push to GitHub, deploy to Cloud Run, Devpost checklist.

Each person: accept GitHub invite → clone their branch → paste Antigravity prompt → `.\scripts\verify_gcp.ps1` → confirm 83 tests pass.
