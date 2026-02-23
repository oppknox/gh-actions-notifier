"""Windows toast notifications via winotify.

Sends native Windows 10/11 toast notifications for completed GitHub Actions
workflow runs, with clickable "View Run" buttons that open the run URL.
"""

from __future__ import annotations

import logging

from winotify import Notification, audio

log = logging.getLogger(__name__)

APP_ID = "GH Actions Notifier"


class Notifier:
    """Sends Windows toast notifications for workflow run completions."""

    def notify_run(self, repo: str, workflow: str, branch: str, conclusion: str, url: str) -> None:
        """Show a toast notification for a single workflow run completion."""
        status = "passed" if conclusion == "success" else "FAILED"
        title = f"{'[PASS]' if conclusion == 'success' else '[FAIL]'} {repo}"
        body = f"{workflow} on {branch} {status}"

        try:
            toast = Notification(
                app_id=APP_ID,
                title=title,
                msg=body,
                duration="short",
            )
            toast.set_audio(
                audio.Default if conclusion == "success" else audio.IM,
                loop=False,
            )
            if url:
                toast.add_actions(label="View Run", launch=url)
            toast.show()
            log.info("Toast: %s — %s", title, body)
        except Exception as e:
            log.error("Failed to show toast: %s", e)

    def notify_summary(self, count: int) -> None:
        """Show a summary toast when notifications are capped per cycle."""
        try:
            toast = Notification(
                app_id=APP_ID,
                title="GitHub Actions",
                msg=f"...and {count} more workflow run(s) completed.",
                duration="short",
            )
            toast.show()
        except Exception as e:
            log.error("Failed to show summary toast: %s", e)
