# GitHub Actions Notifier

Windows system tray app that monitors GitHub Actions workflow runs and sends native toast notifications when they complete.

## Features

- System tray icon with status indicators (green/red/gray/blue)
- Native Windows 10/11 toast notifications with clickable "View Run" links
- GitHub OAuth Device Flow authentication (no secrets in config)
- Configurable allowlist/blocklist for repos
- Rate-limit-aware polling with repo batching
- First-run seeding (no notification flood on first launch)

## Setup

### 1. Create a GitHub OAuth App

1. Go to **GitHub > Settings > Developer settings > OAuth Apps > New OAuth App**
2. Set:
   - **Application name**: `GH Actions Notifier` (or whatever you like)
   - **Homepage URL**: `https://github.com` (anything works)
   - **Authorization callback URL**: `https://github.com` (not used for device flow)
3. Click **Register application**
4. Copy the **Client ID** (you do NOT need a client secret)
5. Under the app settings, check **Enable Device Flow**

### 2. Install

```bash
cd gh-actions-notifier
pip install -r requirements.txt
```

### 3. Configure

Run once to generate the config file, then right-click tray icon > **Open Config**, or edit directly:

```
%APPDATA%\gh-actions-notifier\config.json
```

```json
{
  "client_id": "Ov23li...",
  "poll_interval": 30,
  "allowlist": [],
  "blocklist": []
}
```

- `client_id` **(required)** - Your GitHub OAuth App's Client ID
- `poll_interval` - Seconds between poll cycles (default: 30)
- `allowlist` - If non-empty, ONLY these repos are monitored (e.g. `["owner/repo"]`)
- `blocklist` - Repos to exclude (ignored if allowlist is set)

### 4. Run

```bash
# With console output (for debugging)
python -m gh_actions_notifier

# Windowless (background)
pythonw run.pyw
```

### 5. Authenticate

Right-click tray icon > **Authenticate**. A browser tab opens and the device code is copied to your clipboard. Paste and authorize.

## Tray Menu

| Menu Item      | Action                                      |
|----------------|---------------------------------------------|
| Status line    | Shows connection status                     |
| Authenticate   | Start GitHub OAuth device flow              |
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
