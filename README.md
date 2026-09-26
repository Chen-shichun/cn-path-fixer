# cn-path-fixer

> Diagnose and fix developer-tool breakage caused by non-ASCII (e.g. Chinese) characters in the Windows user profile path.

English | [简体中文](README.zh-CN.md)

## Introduction

On Windows, if your account name contains non-ASCII characters — for example `C:\Users\张三\` — a whole class of developer tools quietly puts their data directories under that path: npm installs global packages and its cache there, conda creates environments and package caches there, and native build toolchains (cmake, MSVC, node-gyp) are frequently invoked from there.

Some of these tools handle it fine. Others do not. The failures are confusing because they rarely say "your username is Chinese": instead you get `path contains non-ASCII characters`, garbled install prefixes, environments that refuse to create, or builds that die with encoding errors deep inside a third-party script.

**cn-path-fixer** is a small, dependency-free helper that:

1. **Diagnoses** — reads the current configuration of npm, conda, git and your build directory, and reports exactly which paths contain non-ASCII characters.
2. **Fixes** — relocates the offending directories onto a pure-ASCII path (default `C:\tools`), with a dry-run mode so you see every change before it happens.
3. **Verifies** — after applying a change it reads the value back from the tool and confirms it actually took effect, instead of assuming success.

It is designed to be conservative: read-only by default, dry-run first, refuse unsafe input, and fully reversible.

## The problem, concretely

Running the diagnostic on an affected machine produces output like this:

```
===== CN-PATH DIAGNOSTIC REPORT =====

USERPROFILE : C:\Users\张三  [NON-ASCII!]

--- npm ---
prefix : C:\Users\张三\AppData\Roaming\npm  [NON-ASCII!]
cache  : C:\Users\张三\AppData\Local\npm-cache  [NON-ASCII!]
```

After the fix, the same diagnostic reports:

```
--- npm ---
prefix : C:\tools\npm  [ascii ok]
cache  : C:\tools\npm-cache  [ascii ok]
```

## Requirements

- Windows (the problem this solves is Windows-specific)
- Python 3.8 or newer — **standard library only**, no packages to install
- `npm` and/or `conda` on `PATH` (optional; each tool is skipped if not installed)

## Installation

Copy the skill folder into your WorkBuddy user skills directory:

```
~/.workbuddy/skills/cn-path-fixer/
```

That is all — there is nothing to build or install.

## Usage

### Step 1 — Diagnose (read-only, always safe)

```bash
python scripts/diagnose.py
```

This never modifies anything. It prints, per tool, whether the relevant path contains non-ASCII characters.

### Step 2 — Preview the fix (dry run)

```bash
python scripts/fix.py -Tool npm -Base C:\tools -DryRun
```

Output:

```
===== CN-PATH FIX (Base: C:\tools, Tool: npm, DryRun: True) =====
[DRYRUN] create dir: C:\tools\npm
[DRYRUN] create dir: C:\tools\npm-cache
[DRYRUN] npm config set prefix C:\tools\npm
[DRYRUN] npm config set cache C:\tools\npm-cache
===== DONE =====
```

### Step 3 — Apply

```bash
python scripts/fix.py -Tool npm -Base C:\tools
```

The script sets the value, then reads it back and prints `[verified]` only if the tool actually reports the new path:

```
npm prefix -> C:\tools\npm  [verified]
npm cache  -> C:\tools\npm-cache  [verified]
```

To also add the new global binary directory to your User PATH:

```bash
python scripts/fix.py -Tool npm -Base C:\tools -AddToPath
```

### Step 4 — Verify

```bash
python scripts/diagnose.py
npm config get prefix
npm root -g
```

Open a **new** terminal for PATH changes to take effect.

## Options

| Option | Values | Default | Description |
|---|---|---|---|
| `-Tool` | `npm`, `conda`, `all` | `all` | Which tool to fix. Tools that are not installed are skipped gracefully. |
| `-Base` | any pure-ASCII path | `C:\tools` | Destination root. Non-ASCII bases are rejected with an error. |
| `-DryRun` | flag | off | Print what would happen without changing anything. |
| `-AddToPath` | flag | off | Append `<BASE>\npm` to the User PATH so globally installed CLIs resolve. |

## What it actually changes

Nothing hidden. Every mutation is one of the following:

**npm** (writes to your `~/.npmrc`)

```bash
npm config set prefix "<BASE>\npm"
npm config set cache  "<BASE>\npm-cache"
```

**conda** (writes to your `~/.condarc`)

```bash
conda config --add envs_dirs "<BASE>\conda-envs"
conda config --add pkgs_dirs "<BASE>\conda-pkgs"
```

**PATH** (only with `-AddToPath`)

Appends `<BASE>\npm` to the per-user `Path` value in the registry. The comparison is done on normalized
paths, so running the script repeatedly will never add duplicate entries.

It does **not** uninstall anything, does not touch Node.js or Python themselves, and does not delete
your old directories. Already-installed packages stay where they are; only *future* global installs
go to the new location.

## Safety

- **Dry-run first.** `-DryRun` shows every command before anything is written.
- **Refuses unsafe input.** A non-ASCII `-Base` is rejected immediately with a non-zero exit code.
- **Verifies, not assumes.** Each setting is read back after being written. A failure is reported as
  `ERROR`, never silently reported as success.
- **Idempotent.** Re-running is safe; PATH entries are de-duplicated.
- **Fully reversible.**

### Rolling back

`~/.npmrc` is a plain text file. Either edit it directly, or run:

```bash
npm config set prefix "<your original prefix>"
npm config set cache  "<your original cache>"
```

For conda, remove the added lines from `~/.condarc`.

## Repository layout

```
cn-path-fixer/
├── README.md                       # This file
├── README.zh-CN.md                 # Chinese documentation
├── SKILL.md                        # Skill manifest (frontmatter + workflow)
├── LICENSE                         # MIT
├── .gitignore
├── scripts/
│   ├── diagnose.py                 # Read-only diagnostic
│   └── fix.py                      # Parameterized fix with dry-run
└── references/
    └── troubleshooting.md          # Per-tool error symptoms and causes
```

## Notes and gotchas

- **`npm config set` is a local file write.** It does not touch the network. If you see `EPERM`,
  that is a permissions or sandbox problem, not connectivity.
- **Prefer Bash + Python over PowerShell for Chinese paths.** On some setups, passing a path
  containing Chinese characters through PowerShell corrupts the argument at the process-launch
  layer. Invoking the scripts from Bash with a managed Python interpreter avoids this entirely.
- **Windows tool output is often GBK-encoded.** The scripts capture subprocess output as bytes and
  decode with a `utf-8 → gbk → latin-1` fallback chain, so Chinese paths are read correctly instead
  of raising a `UnicodeDecodeError`.
- **Your `USERPROFILE` itself cannot be changed** — it is determined by the Windows account name.
  This tool works around it by relocating tool data directories, which is what actually matters.
- **Build/source directories** should still be placed on a pure-ASCII path (e.g. `C:\dev`). The
  diagnostic flags a non-ASCII current working directory as a build risk.

## License

MIT — see [LICENSE](LICENSE).
