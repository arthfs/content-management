---
name: update-progress-log
description: "Use at the start and end of every work session in this repo, or when the user asks what is left, what was done, or to remember/document progress, so later VS Code sessions can resume."
---

# Keep the progress log current

Source of truth: `.github/PROGRESS.md`.

**Start of session**: read it fully. Treat "Decisions" as binding and "Open items" as the backlog.

**During/end of session**:
1. Move completed items from "Open items" to "Done" (one line each, with file paths).
2. Add every unfinished, skipped, unverified, or user-must-do step (credentials to fill, commands not yet run, uncommitted work) to "Open items" as a checkbox.
3. Record new owner decisions under "Decisions" in the owner's words, briefly.
4. Add a dated line to "Log".
5. Never write passwords, tokens, or API keys.
