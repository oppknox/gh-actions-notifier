# GitHub Actions Notifier

Windows system tray app that monitors GitHub Actions workflow runs and sends native toast notifications when they complete.

## Features

- System tray icon with status indicators (green/red/orange/blue)
- Native Windows 10/11 toast notifications with clickable "View Run" links
- Simple Personal Access Token authentication (no OAuth app setup needed)
- Configurable allowlist/blocklist for repos
- Rate-limit-aware polling with repo batching
- First-run seeding (no notification flood on first launch)

## Setup

### 1. Install

```bash
cd gh-actions-notifier
pip install -r requirements.txt
```

### 2. Run

```bash
# With console output (for debugging)
python -m gh_actions_notifier

# Windowless (background)
pythonw run.pyw
```

### 3. Authenticate

Right-click tray icon > **Authenticate**. A browser tab opens to create a GitHub Personal Access Token (with the `repo` scope pre-selected). Generate the token, copy it, and paste it into the dialog.

### 4. Configure (optional)

Right-click tray icon > **Open Config**, or edit directly:

```
%APPDATA%\gh-actions-notifier\config.json
```

```json
{
  "poll_interval": 30,
  "allowlist": [],
  "blocklist": []
}
```

- `poll_interval` - Seconds between poll cycles (default: 30)
- `allowlist` - If non-empty, ONLY these repos are monitored (e.g. `["owner/repo"]`)
- `blocklist` - Repos to exclude (ignored if allowlist is set)

## Tray Menu

| Menu Item      | Action                                      |
|----------------|---------------------------------------------|
| Status line    | Shows connection status                     |
| Authenticate   | Authenticate with a GitHub Personal Access Token |
| Poll Now       | Trigger an immediate poll cycle             |
| Open Config    | Open config.json in default editor          |
| Reload Config  | Reload config without restarting            |
| Open Log       | Open app.log in default editor              |
| Quit           | Clean shutdown                              |

## Files

| Path | Purpose |
|------|---------|
| `%APPDATA%\gh-actions-notifier\config.json` | Configuration |
| `%APPDATA%\gh-actions-notifier\state.json` | Auth token + last-seen run IDs |
| `%APPDATA%\gh-actions-notifier\app.log` | Application log |
