import json
import os
import time
import urllib.request

REPO = "Mohammed-kharbotli/git-aicm"
CHECK_INTERVAL = 86400  # 1 day


def _cache_path():
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "git-aicm")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "latest_version")


def _read_cache():
    path = _cache_path()
    try:
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < CHECK_INTERVAL:
            with open(path) as f:
                return f.read().strip()
    except OSError:
        pass
    return None


def _write_cache(version):
    try:
        with open(_cache_path(), "w") as f:
            f.write(version)
    except OSError:
        pass


def check_for_update(current_version):
    cached = _read_cache()
    if cached:
        latest = cached
    else:
        try:
            url = f"https://api.github.com/repos/{REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                latest = data.get("tag_name", "").lstrip("v")
        except Exception:
            return None
        _write_cache(latest)

    if latest and latest != current_version and _is_newer(latest, current_version):
        return latest
    return None


def _is_newer(latest, current):
    try:
        l = [int(x) for x in latest.split(".")]
        c = [int(x) for x in current.split(".")]
        return l > c
    except (ValueError, AttributeError):
        return False
