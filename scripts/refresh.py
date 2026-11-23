"""Updates every listed mod's latest release.

Usage: python scripts/refresh.py [--local FILE] [--no-push]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import github as gh  # noqa: E402
import indexlib as il  # noqa: E402


def refresh(mods):
    out = []
    for entry in mods:
        try:
            info = gh.repo_info(entry["repo"])
            release = gh.latest_release(entry["repo"]) if info else None
        except Exception as e:  # GitHub hiccup: leave this entry as it was
            print(f"skip {entry.get('id')}: {e}")
            out.append(entry)
            continue
        out.append(il.refresh_entry(entry, release, repo_exists=info is not None))
    return out


def main():
    args = sys.argv[1:]
    path = args[args.index("--local") + 1] if "--local" in args else "mods.json"
    gh.save_mods(refresh(gh.load_mods(path)), path)
    if "--local" not in args and "--no-push" not in args:
        gh.commit_and_push("Refresh latest releases", path)


if __name__ == "__main__":
    main()
