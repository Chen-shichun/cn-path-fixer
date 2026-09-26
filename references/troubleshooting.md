# Troubleshooting: Chinese (non-ASCII) paths in the Windows profile

## Why it happens
Windows derives `%USERPROFILE%` from the account display name. A Chinese account name
produces a path like `C:\Users\张三\`. Tools that default their data directory to
`%USERPROFILE%` (or `%APPDATA%` / `%LOCALAPPDATA%` beneath it) inherit the non-ASCII path.

## npm
- **Symptom:** `npm install -g <pkg>` writes into `C:\Users\张三\AppData\Roaming\npm` and
  the path gets mojibake/garbled when passed to child processes or package scripts; some
  packages fail to install or their shims break. Using `--prefix` under the Chinese path
  produces the same garbling.
- **Cause:** npm's default `prefix`/`cache` live under `%APPDATA%` → Chinese path.
- **Fix:** `npm config set prefix <ascii>` and `npm config set cache <ascii>`
  (e.g. `C:\tools\npm`, `C:\tools\npm-cache`). Add the prefix `bin` to PATH.
- **Rule:** never pass a Chinese path via `--prefix`; always use a pure-ASCII directory.

## conda / Anaconda
- **Symptom:** `conda create -n foo` fails, or the env lands in a path with mojibake;
  `conda env list` shows a path the OS cannot fully resolve; packages with post-install
  scripts that shell out error out.
- **Cause:** default `envs_dirs`/`pkgs_dirs` include a directory under the Chinese profile
  path.
- **Fix:** `conda config --add envs_dirs <ascii>` and `--add pkgs_dirs <ascii>`
  (e.g. `C:\tools\conda-envs`, `C:\tools\conda-pkgs`). New envs are created in the ASCII
  path.

## git
- **Symptom:** `detected dubious repository ownership` when operating on a repo located
  under the Chinese profile path; hooks with shebang lines occasionally misbehave.
- **Cause:** git's safe.directory / ownership checks. Rarer than npm/conda.
- **Fix:** `git config --global --add safe.directory <repo-path>` for the specific repo,
  or keep repos outside the profile path. Git generally tolerates Chinese paths better
  than npm/conda.

## cmake / native builds
- **Symptom:** configure/build fails with "path contains non-ASCII characters" or encoding
  errors in generated files; some MSVC / CUDA / embedded toolchains refuse Chinese paths.
- **Cause:** source or build trees located under the Chinese profile path.
- **Fix (usage rule, not a config change):** place source and build trees in a pure-ASCII
  directory (e.g. `C:\dev\project` or `D:\dev\project`), never under `C:\Users\张三\`.
