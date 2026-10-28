---
name: cn-path-fixer
description: 'Diagnose and fix Windows developer-tool failures caused by non-ASCII characters in user-profile or build paths. Use for npm or conda path failures, garbled install locations, dubious Git ownership, and native-build encoding errors; do not invoke merely because a Windows account name is non-ASCII when no tooling problem exists.'
---

# CN Path Fixer

## Overview
On Windows, the user profile folder is derived from the account display name. When the
account name contains Chinese (or other non-ASCII) characters, the profile path becomes
something like `C:\Users\张三\`. Many developer tools store caches, global packages,
virtual environments, or build artifacts under this path by default and choke on the
non-ASCII characters, producing cryptic failures (garbled paths, "path contains
non-ASCII", environment-creation errors, dubiously-owned repos). This skill detects such
problems and safely relocates the affected tool state onto a pure-ASCII path the user owns.

## Safety / Consent
This skill changes global tool configuration (npm config, conda config, optionally the
User PATH). Always follow this order:
1. Run `scripts/diagnose.py` (read-only) and show the user the findings.
2. Summarize the concrete risk and the exact fix for each affected tool.
3. Ask the user to confirm before applying any change.
4. Apply changes with `scripts/fix.py`, running a `-DryRun` first so the user sees
   exactly what will happen.

Never touch personal file directories (Desktop / Documents / Downloads / Home). This skill
only relocates tool cache/package directories to an ASCII location chosen by the user.

## Workflow

### Step 1 — Diagnose (read-only, safe to run anytime)
From the skill directory, use any available Python 3.8+ interpreter:
```
python scripts/diagnose.py
```
The script reports, per tool, whether its relevant paths contain non-ASCII characters.

### Step 2 — Report & confirm
Present a short table: tool → current (problematic) path → status. For each affected tool,
state the fix and its effect. Wait for explicit user confirmation before proceeding.

### Step 3 — Fix (parameterized, confirmed)
Run `fix.py` from the skill directory. The default base is
`C:\tools` (pure ASCII, normally writable by a standard user). Override with `-Base` if
`C:\tools` is not writable or a non-system drive is preferred (e.g. `D:\tools`).
- Dry run first (shows exactly what will change):
```
python scripts/fix.py -Tool all -Base "C:\tools" -DryRun
```
- Apply:
```
python scripts/fix.py -Tool all -Base "C:\tools"
```
Supported `-Tool` values: `npm`, `conda`, `all`.
For npm, append `-AddToPath` to also add the new prefix directory (`<BASE>\npm`, which is
where npm puts global CLI shims on Windows) to the User PATH so globally installed CLIs
are found.

### Step 4 — Verify
Re-run `diagnose.py` and confirm the affected paths now resolve to ASCII locations. Tell
the user to open a new terminal so the changed config takes effect.

## Reference
For a catalog of the specific error signatures each tool produces under a Chinese path and
why they occur, see `references/troubleshooting.md`.

