#!/usr/bin/env python3
"""Relocate npm / conda data directories onto a pure-ASCII path to avoid
breakage caused by a Chinese (non-ASCII) Windows user profile path.

Usage (run with the managed Python interpreter):
    python fix.py [-Tool npm|conda|all] [-Base C:\\tools] [-DryRun] [-AddToPath]

This changes global tool configuration. Always run -DryRun first and confirm
with the user before applying.
"""
import argparse
import os
import shutil
import subprocess

try:
    import winreg
except Exception:
    winreg = None


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
        r = subprocess.run(cmd, capture_output=True, shell=False, timeout=60)
        return _decode(r.stdout).strip()
    except Exception:
        return None


def run_check(cmd):
    """Run a mutating command; return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, shell=False, timeout=60)
        return r.returncode, _decode(r.stdout).strip(), _decode(r.stderr).strip()
    except Exception as e:
        return -1, "", str(e)


def which(tool):
    return shutil.which(tool)


def ensure_dir(p, dry):
    if not os.path.isdir(p):
        if dry:
            print(f"[DRYRUN] create dir: {p}")
        else:
            os.makedirs(p, exist_ok=True)
            print(f"created dir: {p}")
    else:
        print(f"dir exists: {p}")


def get_user_path():
    if not winreg:
        return ""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(key, "Path")
        winreg.CloseKey(key)
        return val or ""
    except Exception:
        return ""


def set_user_path(val):
    if not winreg:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0,
                             winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, val)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Relocate npm or conda data to an ASCII-only Windows path."
    )
    parser.add_argument("-Tool", "--tool", choices=("npm", "conda", "all"),
                        default="all", type=str.lower)
    parser.add_argument("-Base", "--base", default=r"C:\tools")
    parser.add_argument("-DryRun", "--dry-run", "-dry", action="store_true")
    parser.add_argument("-AddToPath", "--add-to-path", action="store_true")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    tool, base, dry, add_path = args.tool, os.path.normpath(args.base), args.dry_run, args.add_to_path

    if non_ascii(base):
        print(f"ERROR: Base path '{base}' contains non-ASCII characters. "
              "Use a pure-ASCII path (e.g. C:\\tools or D:\\tools).")
        raise SystemExit(1)
    if not os.path.isabs(base) or os.path.dirname(base) == base:
        print("ERROR: Base must be an absolute subdirectory such as C:\\tools.")
        raise SystemExit(1)

    print(f"===== CN-PATH FIX (Base: {base}, Tool: {tool}, DryRun: {dry}) =====")

    if tool in ("npm", "all"):
        if not which("npm"):
            print("npm not found, skipped")
        else:
            np = os.path.join(base, "npm")
            nc = os.path.join(base, "npm-cache")
            ensure_dir(np, dry)
            ensure_dir(nc, dry)
            if dry:
                print(f"[DRYRUN] npm config set prefix {np}")
                print(f"[DRYRUN] npm config set cache {nc}")
            else:
                rc, out, err = run_check(["npm", "config", "set", "prefix", np])
                if rc != 0:
                    print(f"ERROR: failed to set npm prefix: {err or out}")
                else:
                    got = run(["npm", "config", "get", "prefix"])
                    if got and os.path.normpath(got) == os.path.normpath(np):
                        print(f"npm prefix -> {np}  [verified]")
                    else:
                        print(f"WARN: prefix set but readback='{got}' (expected '{np}')")
                rc, out, err = run_check(["npm", "config", "set", "cache", nc])
                if rc != 0:
                    print(f"ERROR: failed to set npm cache: {err or out}")
                else:
                    got = run(["npm", "config", "get", "cache"])
                    if got and os.path.normpath(got) == os.path.normpath(nc):
                        print(f"npm cache  -> {nc}  [verified]")
                    else:
                        print(f"WARN: cache set but readback='{got}' (expected '{nc}')")
                if add_path:
                    cur = get_user_path()
                    # compare normalized paths so mixed separators do not
                    # cause the same directory to be appended twice
                    entries = [p for p in cur.split(";") if p.strip()]
                    norm = [os.path.normpath(p) for p in entries]
                    if os.path.normpath(np) in norm:
                        print(f"{np} already in User PATH")
                    else:
                        new = f"{cur};{np}" if cur else np
                        if set_user_path(new):
                            print(f"added {np} to User PATH (restart terminal to apply)")
                        else:
                            print(f"could not modify User PATH; add '{np}' manually")
                else:
                    print(f"REMINDER: add '{np}' to PATH so global npm CLIs are found.")

    if tool in ("conda", "all"):
        if not which("conda"):
            print("conda not found, skipped")
        else:
            envs = os.path.join(base, "conda-envs")
            pkgs = os.path.join(base, "conda-pkgs")
            ensure_dir(envs, dry)
            ensure_dir(pkgs, dry)
            if dry:
                print(f"[DRYRUN] conda config --add envs_dirs {envs}")
                print(f"[DRYRUN] conda config --add pkgs_dirs {pkgs}")
            else:
                rc, out, err = run_check(["conda", "config", "--add", "envs_dirs", envs])
                if rc != 0:
                    print(f"ERROR: failed to add conda envs_dirs: {err or out}")
                else:
                    print(f"conda envs_dirs -> added {envs}  [cmd rc=0]")
                rc, out, err = run_check(["conda", "config", "--add", "pkgs_dirs", pkgs])
                if rc != 0:
                    print(f"ERROR: failed to add conda pkgs_dirs: {err or out}")
                else:
                    print(f"conda pkgs_dirs -> added {pkgs}  [cmd rc=0]")

    print("===== DONE =====")


if __name__ == "__main__":
    main()

