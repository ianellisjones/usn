#!/usr/bin/env python3
"""
DVIDS Keyword Watcher
=====================

Searches DVIDS (news, images, videos) for ship names or keywords and shows the
posts that are new since your last check. Runs locally in Terminal; standard
library only, nothing to install.

Usage:
    python3 dvids_watch.py "USS Abraham Lincoln"              # check every 5 minutes
    python3 dvids_watch.py "USS Abraham Lincoln" -i 15        # check every 15 minutes
    python3 dvids_watch.py "USS Abraham Lincoln" --daily      # check once a day
    python3 dvids_watch.py "USS Abraham Lincoln" --once       # check once and exit
    python3 dvids_watch.py "USS Abraham Lincoln" "USS Nimitz" # several keywords

Uses the official DVIDS API with your free API key. The first run asks for the
key and saves it to ~/.dvids_api_key (or set the DVIDS_API_KEY environment
variable). Posts already shown are remembered in ~/.ship_watch.

Created for @ianellisjones / IEJ Media.
"""

import argparse
import getpass
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API_SEARCH = "https://api.dvidshub.net/search"
USER_AGENT = "DVIDS-Watch/1.0 (Python; personal keyword watcher)"
CONTENT_TYPES = ["news", "image", "video"]
LOOKBACK_DAYS = 7
MAX_RESULTS = 50
KEY_FILE = os.path.expanduser("~/.dvids_api_key")
STATE_DIR = os.path.expanduser("~/.ship_watch")
SHOW_ON_FIRST_RUN = 10


class KeyRejected(Exception):
    pass


def load_key():
    key = os.environ.get("DVIDS_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            return f.read().strip()
    if not sys.stdin.isatty():
        sys.exit("No DVIDS API key: set DVIDS_API_KEY or run once in Terminal to enter it.")
    print("Paste your DVIDS API key. Log in at https://api.dvidshub.net to see it.")
    key = getpass.getpass("API key (hidden as you paste): ").strip()
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key + "\n")
    print(f"Saved to {KEY_FILE}\n")
    return key


def search(key, keyword, content_type, from_date):
    """One DVIDS search call. Never prints the URL, since it contains the key."""
    params = {"q": keyword, "type": content_type, "max_results": MAX_RESULTS,
              "sort": "publishdate", "sortdir": "desc", "from_date": from_date, "api_key": key}
    req = urllib.request.Request(f"{API_SEARCH}?{urllib.parse.urlencode(params)}",
                                 headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp).get("results") or []
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise KeyRejected()
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** attempt + 1)
                continue
            raise
    return []


def clean(text):
    return " ".join(re.sub(r"<[^>]+>", " ", text or "").split())


def normalize(raw):
    kind = raw.get("type", "")
    item_id = str(raw.get("id", ""))
    keywords = raw.get("keywords") or ""
    if isinstance(keywords, list):
        keywords = ", ".join(keywords)
    city, state, country = raw.get("city", ""), raw.get("state", ""), raw.get("country", "")
    place = ", ".join(p for p in (city, state if country in ("US", "United States") else "", country) if p)
    return {
        "id": item_id,
        "type": kind,
        "title": clean(raw.get("title")) or "Untitled",
        "text": clean(raw.get("description") or raw.get("short_description")),
        "unit": raw.get("unit_name", ""),
        "keywords": keywords,
        "date": raw.get("date_published") or raw.get("date") or "",
        "place": place or "location not given",
        "url": raw.get("url") or f"https://www.dvidshub.net/{kind}/{item_id.split(':')[-1]}",
    }


def matches(item, keyword):
    """DVIDS fulltext search is loose, so confirm the post really mentions the keyword."""
    needle = re.sub(r"\s*\([^)]*\)", "", keyword.lower())
    needle = re.sub(r"^uss\s+", "", needle).strip()
    haystack = " ".join((item["title"], item["text"], item["unit"], item["keywords"])).lower()
    return needle in haystack


def parse_date(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def when(item):
    dt = parse_date(item["date"])
    return dt.astimezone().strftime("%b %d %H:%M") if dt else (item["date"] or "date n/a")


def show(item):
    print(f"  {when(item):<12} {item['type'].upper():<5}  {item['place']}")
    print(f"               {item['title']}")
    print(f"               {item['url']}")


def notify(title, msg):
    print("\a", end="", flush=True)
    if sys.platform == "darwin":
        try:
            subprocess.run(["osascript", "-e", f"display notification {json.dumps(msg)} "
                            f"with title {json.dumps(title)} sound name \"Glass\""], timeout=5)
            subprocess.Popen(["say", msg])
        except Exception:
            pass


def stamp():
    return datetime.now().strftime("%b %d %H:%M")


def fetch(key, keyword):
    from_date = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = {}
    for kind in CONTENT_TYPES:
        for raw in search(key, keyword, kind, from_date):
            item = normalize(raw)
            if item["id"] and matches(item, keyword):
                found[item["id"]] = item
        time.sleep(0.3)
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(found.values(), key=lambda i: parse_date(i["date"]) or epoch, reverse=True)


def check(key, keyword):
    try:
        items = fetch(key, keyword)
    except KeyRejected:
        raise
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            print("Python can't verify HTTPS certificates. If you installed Python from python.org, run:\n"
                  '  open "/Applications/Python 3"*/"Install Certificates.command"')
        else:
            print(f"[{stamp()}] {keyword}: couldn't reach DVIDS ({e}). Will try again next time.")
        return
    except Exception as e:
        print(f"[{stamp()}] {keyword}: DVIDS search failed ({e}). Will try again next time.")
        return

    os.makedirs(STATE_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
    path = os.path.join(STATE_DIR, f"dvids-{slug}.json")
    first_run = not os.path.exists(path)
    seen = set()
    if not first_run:
        with open(path) as f:
            seen = set(json.load(f).get("seen", []))

    new = [i for i in items if i["id"] not in seen]
    with open(path, "w") as f:
        json.dump({"keyword": keyword, "seen": sorted(seen | {i["id"] for i in items})[-2000:]}, f)

    if first_run:
        print(f"[{stamp()}] Now watching DVIDS for \"{keyword}\": {len(items)} posts in the past {LOOKBACK_DAYS} days.")
        if items:
            print(f"  Latest {min(len(items), SHOW_ON_FIRST_RUN)}:")
            for item in items[:SHOW_ON_FIRST_RUN]:
                show(item)
        return
    if not new:
        latest = f" (latest: {when(items[0])}, {items[0]['place']})" if items else ""
        print(f"[{stamp()}] \"{keyword}\": no new posts{latest}")
        return
    print("\n" + "=" * 70)
    print(f"[{stamp()}] *** {len(new)} NEW DVIDS POST(S) for \"{keyword}\" ***")
    for item in new:
        show(item)
    print("=" * 70 + "\n")
    notify(f"DVIDS: {keyword}", f"{len(new)} new DVIDS post{'s' if len(new) != 1 else ''} for {keyword}")


def run_all(key, keywords):
    try:
        for keyword in keywords:
            check(key, keyword)
        return True
    except KeyRejected:
        print("DVIDS rejected the API key. Check it at https://api.dvidshub.net")
        if not os.environ.get("DVIDS_API_KEY") and os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
            print(f"Removed the saved key ({KEY_FILE}); run again to enter it.")
        return False


def main(argv):
    ap = argparse.ArgumentParser(description="Watch DVIDS for new posts about a ship or keyword")
    ap.add_argument("keywords", nargs="+", help='e.g. "USS Abraham Lincoln"')
    ap.add_argument("-i", "--interval", type=float, default=5, help="minutes between checks (default 5)")
    ap.add_argument("--daily", action="store_true", help="check once a day")
    ap.add_argument("--once", action="store_true", help="check once and exit")
    args = ap.parse_args(argv[1:])
    key = load_key()

    if args.once:
        return 0 if run_all(key, args.keywords) else 1

    every = 24 * 60 * 60 if args.daily else max(1.0, args.interval) * 60
    label = "once a day" if args.daily else f"every {args.interval:g} min"
    print(f"[{stamp()}] Checking DVIDS {label} for: {', '.join(args.keywords)}. "
          "Leave this window open; Ctrl+C to stop.")
    last = 0.0
    while True:
        # Wake every minute and check once the interval has passed by the wall
        # clock, so the schedule doesn't drift while the Mac is asleep.
        if time.time() - last >= every:
            last = time.time()
            if not run_all(key, args.keywords):
                return 1
        time.sleep(min(every, 60))


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\nstopped.")
