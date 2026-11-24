"""Runs on a new or edited submission issue: checks it and adds the mod to mods.json.

The person who added a mod, or the owner of its repo, can submit it again to update its listing."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import github as gh  # noqa: E402
import indexlib as il  # noqa: E402

OK = "Listed! It will show up in Mod Manager within a few minutes."
UPDATED = "Updated! The new details show up in Mod Manager within a few minutes."


def check(fields, mods, submitter=None, admin=None):
    """Returns (entry, None) or (None, reason). An owner re-submitting a listed mod gets the updated entry."""
    repo = il.parse_repo(fields.get("repo", ""))
    if not repo:
        return None, il.BAD_LINK
    info = gh.repo_info(repo)
    if not info:
        return None, il.BAD_LINK
    fields = dict(fields, repo=info["full_name"])
    release = gh.latest_release(info["full_name"])
    if release:
        assets = il.latest_block(release)["assets"]
        if assets and not any(a["name"].lower().endswith(".dll") for a in assets):
            if not il.zip_has_dll(gh.download(assets[0]["url"])):
                return None, il.NO_FILES
    listed = next((m for m in mods if m.get("id") == info["full_name"].lower()), None)
    mine = listed is not None and (submitter or "").lower() in il.owners(listed, admin)
    existing = {m["id"] for m in mods if not (mine and m is listed)}
    entry, reason = il.validate_submission(fields, existing, release, submitter=submitter)
    if reason == il.LISTED and listed is not None:
        reason = il.NOT_YOURS_EDIT.format(who=il._owner_names(listed), name=listed.get("name", listed["id"]))
    if entry and mine:
        entry = il.update_listing(listed, entry)
    return entry, reason


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as f:
        issue = json.load(f)["issue"]
    number = issue["number"]
    submitter = (issue.get("user") or {}).get("login")
    repo = os.environ["GITHUB_REPOSITORY"]
    mods = gh.load_mods()
    entry, reason = check(il.parse_issue_form(issue.get("body") or ""), mods, submitter, admin=repo.split("/")[0])
    if reason:
        gh.call("POST", f"/repos/{repo}/issues/{number}/comments",
                {"body": f"Couldn't list this mod: {reason} Edit the issue to try again."})
        return
    updating = any(m.get("id") == entry["id"] for m in mods)
    gh.save_mods(il.add_entry(mods, entry))
    # No "closes #N" here: GitHub would close the issue itself and the close below would fail.
    gh.commit_and_push(f"{'Update' if updating else 'Add'} {entry['name']} ({entry['repo']}) (#{number})")
    gh.call("POST", f"/repos/{repo}/issues/{number}/comments", {"body": UPDATED if updating else OK})
    gh.close_issue(repo, number)


if __name__ == "__main__":
    main()
