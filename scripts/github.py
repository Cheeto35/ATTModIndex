"""Tiny GitHub REST client for the list's Actions (standard library only)."""
import json
import os
import subprocess
import urllib.error
import urllib.request

API = "https://api.github.com"


def _headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "ATTModIndex",
         "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def call(method, path, body=None):
    """Returns (status, json-or-None). 404 comes back as a status; other HTTP errors raise."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 404, None
        raise


def repo_info(repo):
    status, info = call("GET", f"/repos/{repo}")
    return info if status == 200 and info and not info.get("private") else None


def latest_release(repo):
    status, rel = call("GET", f"/repos/{repo}/releases/latest")
    return rel if status == 200 else None


def download(url, limit=50 * 1024 * 1024):
    req = urllib.request.Request(url, headers={"User-Agent": "ATTModIndex"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(limit + 1)


def load_mods(path="mods.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mods(mods, path="mods.json"):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(mods, f, indent=2, ensure_ascii=False)
        f.write("\n")


def commit_and_push(message, path="mods.json"):
    def run(*args):
        subprocess.run(["git", *args], check=True)
    run("config", "user.name", "github-actions[bot]")
    run("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("add", path)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return False
    run("commit", "-m", message)
    run("pull", "--rebase")
    run("push")
    return True


def close_issue(repo, number):
    """Closes an issue; fine if GitHub already closed it."""
    try:
        call("PATCH", f"/repos/{repo}/issues/{number}", {"state": "closed", "state_reason": "completed"})
    except urllib.error.HTTPError as e:
        if e.code != 422:
            raise
