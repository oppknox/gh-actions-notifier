"""Background polling loop for workflow run completions.

Polls GitHub for completed workflow runs across all (or filtered) repos,
tracks which runs have already been seen, and sends toast notifications
for new completions. First-run seeding prevents notification floods.
"""

from __future__ import annotations

import logging
import time

log = logging.getLogger(__name__)

REPO_CACHE_TTL = 600  # 10 minutes
MAX_REPOS_PER_CYCLE = 30
MAX_NOTIFICATIONS_PER_CYCLE = 5


class Poller:
    """Polls GitHub repos for completed workflow runs and triggers notifications."""

    def __init__(self, app, config: dict, state, github, notifier) -> None:
        self._app = app
        self.config = config
        self._state = state
        self._github = github
        self._notifier = notifier
        self._repo_cache: list[dict] = []
        self._repo_cache_time: float = 0
        self._repo_offset: int = 0

    def clear_repo_cache(self) -> None:
        """Force a fresh repo list fetch on the next poll cycle."""
        self._repo_cache = []
        self._repo_cache_time = 0

    def _get_repos(self) -> list[dict]:
        """Return the cached repo list, refreshing if stale."""
        now = time.time()
        if self._repo_cache and (now - self._repo_cache_time) < REPO_CACHE_TTL:
            return self._repo_cache

        repos = self._github.get_repos()
        if not repos:
            return self._repo_cache  # Keep stale cache if API fails

        # Filter by allowlist/blocklist
        allowlist = self.config.get("allowlist", [])
        blocklist = self.config.get("blocklist", [])

        if allowlist:
            repos = [r for r in repos if r["full_name"] in allowlist]
        elif blocklist:
            repos = [r for r in repos if r["full_name"] not in blocklist]

        self._repo_cache = repos
        self._repo_cache_time = now
        self._repo_offset = 0
        log.info("Refreshed repo list: %d repos", len(repos))
        return repos

    def poll_once(self) -> None:
        """Run a single poll cycle across a batch of repos."""
        if not self._state.token:
            return

        repos = self._get_repos()
        if not repos:
            return

        # Rate-limit-aware batching: poll a subset each cycle
        batch = repos
        if len(repos) > MAX_REPOS_PER_CYCLE:
            start = self._repo_offset % len(repos)
            batch = repos[start : start + MAX_REPOS_PER_CYCLE]
            if len(batch) < MAX_REPOS_PER_CYCLE:
                batch += repos[: MAX_REPOS_PER_CYCLE - len(batch)]
            self._repo_offset = (start + MAX_REPOS_PER_CYCLE) % len(repos)

        notification_count = 0

        for repo in batch:
            full_name = repo["full_name"]
            if "/" not in full_name:
                log.warning("Skipping repo with unexpected name: %s", full_name)
                continue
            owner, name = full_name.split("/", 1)
            last_seen = self._state.get_last_seen_id(full_name)

            runs = self._github.get_completed_runs(owner, name, since_id=last_seen)
            if not runs:
                continue

            # Update last seen to highest run ID
            max_id = max(r["id"] for r in runs)
            self._state.set_last_seen_id(full_name, max_id)

            # First-run seeding: record baseline without notifying
            if last_seen == 0:
                log.info("Seeded %s with run ID %d", full_name, max_id)
                continue

            # Only notify on success and failure (skip cancelled, skipped, etc.)
            notifiable = [r for r in runs if r.get("conclusion") in ("success", "failure")]

            for i, run in enumerate(notifiable):
                if notification_count >= MAX_NOTIFICATIONS_PER_CYCLE:
                    remaining = len(notifiable) - i
                    if remaining > 0:
                        self._notifier.notify_summary(remaining)
                    return

                self._notifier.notify_run(
                    repo=full_name,
                    workflow=run.get("name", "Unknown"),
                    branch=run.get("head_branch", "?"),
                    conclusion=run["conclusion"],
                    url=run.get("html_url", ""),
                )
                notification_count += 1

        if notification_count:
            log.info("Sent %d notification(s) this cycle", notification_count)
