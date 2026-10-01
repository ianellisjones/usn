#!/usr/bin/env python3
"""
Ship History Watcher
====================

Checks a ship's history page on uscarriers.net and shows what's new since your
last check. Runs locally in Terminal; standard library only, nothing to install.

Usage:
    python3 ship_watch.py cvn73             # check once: shows new lines since last check
    python3 ship_watch.py cvn73 --daily     # keep running, check once a day
    python3 ship_watch.py cvn73 cvn78       # several ships

The first check saves the page as a baseline. A plain-text copy of each page
is kept in ~/.ship_watch to compare against next time.

uscarriers.net refuses requests from cloud servers (e.g. GitHub Actions),
so this needs to run from your own computer.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from html.parser import HTMLParser

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STATE_DIR = os.path.expanduser("~/.ship_watch")
DAY = 24 * 60 * 60
MAX_NEW_LINES = 40

# Same status words as uscn_last_entry.py, used to pick out the latest entries.
STATUS_KEYWORDS = [
    "moored", "anchored", "underway", "arrived", "departed", "transited",
    "operations", "returned", "participated", "conducted", "moved", "visited",
    "pulled into", "sea trials", "deployed", "port call", "homeport",
]


class TextLines(HTMLParser):
    """Collect each block of visible text on its own line, skipping scripts/styles."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            text = " ".join(data.split())
            if text:
                self.lines.append(text)


def page_url(hull):
    return f"https://uscarriers.net/{hull}history.htm"


def fetch_lines(hull):
    req = urllib.request.Request(page_url(hull), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    parser = TextLines()
    parser.feed(html)
    return parser.lines


def latest_entries(lines, n=3):
    hits = [ln for ln in lines if any(k in ln.lower() for k in STATUS_KEYWORDS)]
    return hits[-n:]


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


def check(hull):
    hull = hull.lower()
    name = hull.upper()
    try:
        lines = fetch_lines(hull)
    except urllib.error.HTTPError as e:
        print(f"[{stamp()}] {name}: uscarriers.net refused the request (HTTP {e.code}). "
              f"Open {page_url(hull)} in your browser instead.")
        return
    except Exception as e:
        print(f"[{stamp()}] {name}: couldn't load the page ({e}). Will try again next time.")
        return

    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f"{hull}.txt")

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[{stamp()}] {name}: now watching {page_url(hull)} ({len(lines)} lines saved). Latest entries:")
        for ln in latest_entries(lines):
            print(f"    {ln}")
        return

    with open(path) as f:
        old = f.read().splitlines()
    if len(lines) < len(old) // 2:
        print(f"[{stamp()}] {name}: page came back much shorter than usual ({len(lines)} lines vs "
              f"{len(old)}), maybe a block or error page. Not saving it; will try again next time.")
        return

    seen = set(old)
    new = [ln for ln in lines if ln not in seen]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

    if not new:
        print(f"[{stamp()}] {name}: no new entries")
        return
    print("\n" + "=" * 70)
    print(f"[{stamp()}] *** {name} HISTORY UPDATED: {len(new)} new line(s) ***")
    for ln in new[:MAX_NEW_LINES]:
        print(f"  + {ln}")
    if len(new) > MAX_NEW_LINES:
        print(f"  ...and {len(new) - MAX_NEW_LINES} more")
    print(f"  {page_url(hull)}")
    print("=" * 70 + "\n")
    notify(f"{name} history updated", f"{name} has {len(new)} new line(s) on uscarriers.net")


def main(argv):
    daily = "--daily" in argv
    hulls = [a for a in argv[1:] if not a.startswith("--")]
    if not hulls:
        print(__doc__)
        return 1

    if not daily:
        for hull in hulls:
            check(hull)
        return 0

    print(f"[{stamp()}] Checking {', '.join(h.upper() for h in hulls)} once a day. "
          "Leave this window open; Ctrl+C to stop.")
    last = 0.0
    while True:
        # Wake every 10 minutes and check once 24h have passed by the wall clock,
        # so the schedule doesn't drift while the Mac is asleep.
        if time.time() - last >= DAY:
            last = time.time()
            for hull in hulls:
                check(hull)
        time.sleep(600)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\nstopped.")
