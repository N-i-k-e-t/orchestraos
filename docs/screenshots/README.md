# Screenshot Guide

Capture these screenshots for the hackathon submission and README. Save as PNG (1920×1080 or browser viewport).

## Required shots

| # | Filename | How to capture |
|---|----------|----------------|
| 1 | `01-demo-two-pane.png` | Dashboard → Demo page. Show rose LEFT (Unprotected) vs emerald RIGHT (Protected) with 99.1% cost reduction. |
| 2 | `02-demo-live-log.png` | Click **Run live demo**. Capture protected recovery log with breaker trip + remediation steps. |
| 3 | `03-incidents.png` | Dashboard → Incidents tab. Show loop + breaker_trip + recovery entries. |
| 4 | `04-metrics.png` | Dashboard → Metrics tab. Show cost saved and session stats. |
| 5 | `05-architecture.png` | README mermaid diagram or `docs/ARCHITECTURE.md` pipeline section (browser or export). |
| 6 | `06-tests-passing.png` | Terminal: `poetry run pytest tests/ -v` showing **79 passed**. |

## Optional shots

| # | Filename | How to capture |
|---|----------|----------------|
| 7 | `07-docker-compose.png` | `docker compose ps` — all services healthy |
| 8 | `08-cloud-run.png` | GCP Console → Cloud Run — 7 services deployed |
| 9 | `09-collector-health.png` | Browser or curl: collector `/health` JSON |
| 10 | `10-arize-phoenix.png` | Arize Phoenix UI showing exported traces (if configured) |

## Capture steps (Windows)

### Dashboard screenshots

```powershell
# Start dashboard
poetry run orchestraos-dashboard

# Open http://localhost:8080 in Chrome/Edge
# Win+Shift+S → rectangular snip → save to docs/screenshots/
```

### Terminal screenshot

```powershell
poetry run pytest tests/ -v
# Win+Shift+S to capture terminal output
```

## Using screenshots in README

After capturing, add to README:

```markdown
## Screenshots

![Demo comparison](docs/screenshots/01-demo-two-pane.png)
![Live recovery log](docs/screenshots/02-demo-live-log.png)
```

## GIF alternative (optional)

Record a 15-second GIF of clicking **Run live demo** with ScreenToGif or Loom clip. Save as `docs/screenshots/demo-live.gif`.
