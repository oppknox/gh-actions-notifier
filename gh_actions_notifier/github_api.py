"""GitHub REST API client with pagination and rate limit awareness."""

import logging
import time

import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


class GitHubClient:
    def __init__(self, state) -> None:
        self._state = state
        self.rate_remaining: int | None = None
        self.rate_reset: float = 0

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = self._state.token
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _update_rate_limit(self, resp: requests.Response) -> None:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None:
            self.rate_remaining = int(remaining)
        reset = resp.headers.get("X-RateLimit-Reset")
        if reset is not None:
            self.rate_reset = float(reset)

    def _check_rate_limit(self) -> bool:
        """Returns True if we should proceed, False if rate limited."""
        if self.rate_remaining is not None and self.rate_remaining < 10:
            wait = max(0, self.rate_reset - time.time())
            if wait > 0:
                log.warning("Rate limited, reset in %.0fs", wait)
                return False
        return True

    def _get(self, url: str, params: dict | None = None) -> requests.Response | None:
        if not self._check_rate_limit():
            return None
        try:
            resp = requests.get(
                url if url.startswith("http") else f"{API_BASE}{url}",
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            self._update_rate_limit(resp)
            if resp.status_code == 401:
                log.error("Token invalid (401)")
                return None
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.error("API request failed: %s", e)
            return None

    def get_user(self) -> str | None:
        """Validate token, returns username or None."""
        resp = self._get("/user")
        if resp is None:
            return None
        return resp.json().get("login")

    def get_repos(self) -> list[dict]:
        """Get all repos the user has access to (paginated)."""
        repos = []
        url = "/user/repos"
        params = {"per_page": 100, "sort": "pushed"}

        while url:
            resp = self._get(url, params=params)
            if resp is None:
                break
            repos.extend(resp.json())
            params = None  # Only needed for first request
            # Parse Link header for next page
            url = self._next_page_url(resp)

        return repos

    def get_completed_runs(self, owner: str, repo: str, since_id: int = 0) -> list[dict]:
        """Get recent completed workflow runs for a repo."""
        resp = self._get(
            f"/repos/{owner}/{repo}/actions/runs",
            params={"status": "completed", "per_page": 25},
        )
        if resp is None:
            return []

        runs = resp.json().get("workflow_runs", [])
        # Filter to only runs newer than since_id
        if since_id:
            runs = [r for r in runs if r["id"] > since_id]
        return runs

    @staticmethod
    def _next_page_url(resp: requests.Response) -> str | None:
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                return url
        return None
