#!/usr/bin/env python3
"""Read-only diagnostic: detect non-ASCII (e.g. Chinese) characters in the
Windows user profile path and in the data directories used by npm, conda,
git and cmake. Safe to run anytime - it only reads configuration."""
import os
import subprocess
import sys


def non_ascii(p):
    return bool(p) and any(ord(c) > 127 for c in p)


def _decode(b):
    if not b:
        return ""
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", "replace")


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, shell=True, timeout=30)
        return _decode(r.stdout).strip()
    except Exception:
        return None


def which(tool):
    return run(f"command -v {tool}") or run(f"where {tool}")


def main():
    print("===== CN-PATH DIAGNOSTIC REPORT =====")

    profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    print()
    tag = "[NON-ASCII!]" if non_ascii(profile) else "[ascii ok]"
    print(f"USERPROFILE : {profile}  {tag}")
    home = os.environ.get("HOME")
    if home:
        tag = "[NON-ASCII!]" if non_ascii(home) else "[ascii ok]"
        print(f"HOME (git)  : {home}  {tag}")

    print("\n--- npm ---")
    if not which("npm"):
        print("npm not found, skipped")
    else:
        prefix = run("npm config get prefix")
        cache = run("npm config get cache")
        print(f"prefix : {prefix}  { '[NON-ASCII!]' if non_ascii(prefix) else '[ascii ok]'}")
        print(f"cache  : {cache}  { '[NON-ASCII!]' if non_ascii(cache) else '[ascii ok]'}")

    print("\n--- conda ---")
    if not which("conda"):
        print("conda not found, skipped")
    else:
        info = run("conda info --json")
        try:
            import json
            d = json.loads(info)
            for p in d.get("envs_dirs", []):
                print(f"envs_dirs: {p}  { '[NON-ASCII!]' if non_ascii(p) else '[ascii ok]'}")
            for p in d.get("pkgs_dirs", []):
                print(f"pkgs_dirs: {p}  { '[NON-ASCII!]' if non_ascii(p) else '[ascii ok]'}")
        except Exception:
            print("conda info parse failed")

    print("\n--- git ---")
    if not which("git"):
        print("git not found, skipped")
    else:
        sd = run("git config --global --get-all safe.directory")
        if sd:
            print("safe.directory: " + sd.replace("\n", ", "))
        print("note: git tolerates Chinese paths better than npm/conda, but repos "
              "under a Chinese path may trigger 'dubious ownership'.")

    print("\n--- cmake / build dir ---")
    if which("cmake"):
        v = run("cmake --version")
        print("cmake: " + (v.splitlines()[0] if v else "?"))
    cwd = os.getcwd()
    tag = "[NON-ASCII! build may fail]" if non_ascii(cwd) else "[ascii ok]"
    print(f"current dir: {cwd}  {tag}")
    print("note: keep source/build trees in a pure-ASCII path (e.g. C:\\dev) "
          "to avoid toolchain encoding errors.")

    print("\n===== END =====")


if __name__ == "__main__":
    main()
    sys.exit(0)
