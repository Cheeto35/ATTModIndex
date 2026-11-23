"""Pure helpers for the mod list: reading submissions, checking them, and building list entries."""
import datetime
import io
import re
import zipfile

SIDES = ("client", "server", "both")
LABELS = {"repository url": "repo", "mod name": "name", "description": "description", "side": "side",
          "tags": "tags"}
NO_RESPONSE = "_No response_"

BAD_LINK = "That doesn't look like a GitHub repo link."
LISTED = "This mod is already listed."
NO_RELEASE = "The repo has no releases yet."
NO_FILES = "The latest release has no .dll or .zip file attached."
BAD_SIDE = "Pick client, server or both for Side."
NO_NAME = "Mod name is required."

_NAME = r"[A-Za-z0-9_.-]+"
_REPO_RE = re.compile(r"^(?:(?:https?://)?(?:www\.)?github\.com/)?(" + _NAME + r")/(" + _NAME + r")(?:/.*)?$")


def parse_repo(text):
    """Same rules as the launcher addon: 'https://github.com/Owner/Repo/...' or 'Owner/Repo'."""
    text = (text or "").strip()
    if not text or " " in text:
        return None
    if "://" in text or "." in text.split("/")[0]:
        if not re.match(r"^(?:https?://)?(?:www\.)?github\.com/", text, re.I):
            return None
    elif text.count("/") != 1:
        return None
    m = _REPO_RE.match(text)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    return f"{owner}/{repo}" if repo else None


def parse_issue_form(body):
    out = {}
    key = None
    lines = []
    for line in (body or "").replace("\r\n", "\n").split("\n") + ["### "]:
        if line.startswith("### "):
            if key:
                value = "\n".join(lines).strip()
                out[key] = "" if value == NO_RESPONSE else value
            key = LABELS.get(line[4:].strip().lower())
            lines = []
        elif key:
            lines.append(line)
    return out


def _ext(name):
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def latest_block(release):
    assets = [{"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)}
              for a in release.get("assets", []) if _ext(a.get("name", "")) in ("dll", "zip")]
    return {"tag": release.get("tag_name"), "published": (release.get("published_at") or "")[:10],
            "assets": assets}


def zip_has_dll(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return any(n.lower().endswith(".dll") for n in z.namelist())
    except zipfile.BadZipFile:
        return False


def _tags(text):
    out = []
    for t in (text or "").split(","):
        t = t.strip().lower()[:24]
        if t and t not in out:
            out.append(t)
    return out[:5]


def validate_submission(fields, existing_ids, release, today=None):
    repo = parse_repo(fields.get("repo", ""))
    if not repo:
        return None, BAD_LINK
    name = (fields.get("name") or "").strip()
    if not name:
        return None, NO_NAME
    side = (fields.get("side") or "").strip().lower()
    if side not in SIDES:
        return None, BAD_SIDE
    mod_id = repo.lower()
    if mod_id in {i.lower() for i in existing_ids}:
        return None, LISTED
    if not release:
        return None, NO_RELEASE
    latest = latest_block(release)
    if not latest["assets"]:
        return None, NO_FILES
    return {"id": mod_id, "name": name[:60], "repo": repo, "author": repo.split("/")[0],
            "description": " ".join((fields.get("description") or "").split())[:200], "side": side,
            "tags": _tags(fields.get("tags")), "added": today or datetime.date.today().isoformat(),
            "latest": latest}, None


def add_entry(mods, entry):
    mods = [m for m in mods if m.get("id") != entry["id"]] + [entry]
    return sorted(mods, key=lambda m: m.get("id", ""))


def refresh_entry(entry, release, repo_exists):
    entry = dict(entry)
    latest = latest_block(release) if (repo_exists and release) else None
    if not latest or not latest["assets"]:
        entry["unavailable"] = True
        return entry
    entry["latest"] = latest
    entry.pop("unavailable", None)
    return entry
