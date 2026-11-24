"""Runs on a removal issue: takes a mod off the list if the issue's author added it or owns its repo."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import github as gh  # noqa: E402
import indexlib as il  # noqa: E402

REMOVED = "Removed. It will disappear from Mod Manager within a few minutes."


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as f:
        issue = json.load(f)["issue"]
    number = issue["number"]
    who = (issue.get("user") or {}).get("login")
    repo = os.environ["GITHUB_REPOSITORY"]
    mods = gh.load_mods()
    entry, reason = il.validate_removal(il.parse_issue_form(issue.get("body") or ""), mods, who,
                                       admin=repo.split("/")[0])
    if reason:
        gh.call("POST", f"/repos/{repo}/issues/{number}/comments",
                {"body": f"Couldn't remove this mod: {reason}"})
        return
    gh.save_mods(il.remove_entry(mods, entry["id"]))
    gh.commit_and_push(f"Remove {entry['name']} ({entry['repo']}) (#{number})")
    gh.call("POST", f"/repos/{repo}/issues/{number}/comments", {"body": REMOVED})
    gh.close_issue(repo, number)


if __name__ == "__main__":
    main()
