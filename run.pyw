"""Windowless entry point - run with pythonw.exe for no console window."""

from gh_actions_notifier.app import Application

app = Application()
app.run()
