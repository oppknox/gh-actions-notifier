"""Entry point for `python -m gh_actions_notifier`."""

from .app import Application


def main() -> None:
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
