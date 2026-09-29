#!/usr/bin/env python3
"""
Ship History Watcher
====================

Checks ship history pages on uscarriers.net (e.g. cvn73 -> cvn73history.htm)
and reports when a page has changed since the last check.

For each hull it saves ship_watch/<hull>.json holding the newest entry
(found with uscn_last_entry.py) and a short hash of every line on the page.
Only hashes are stored, never the page text, so the next run can show exactly
which lines are new without keeping a copy of the site's content.

When anything changed, it writes ship_watch_issue.md (first line = title,
rest = body) for the GitHub workflow to post as an issue.

Usage:
    python ship_watch.py cvn73               # check, update state, write issue file
    python ship_watch.py cvn73 cvn78         # several ships
    python ship_watch.py cvn73 --dry-run     # check and print only, change nothing
"""

import hashlib
import json
import os
import sys
import time

from uscn_last_entry import extract_date, fetch_full_text, find_last_entry, find_location

STATE_DIR = "ship_watch"
ISSUE_FILE = "ship_watch_issue.md"
MAX_NEW_LINES = 40  # cap on new lines quoted in one issue


def line_hash(line: str) -> str:
    return hashlib.sha1(line.encode("utf-8")).hexdigest()[:12]


def page_url(hull: str) -> str:
    return f"http://uscarriers.net/{hull.lower()}history.htm"


def fetch_with_retry(hull: str) -> str:
    try:
        return fetch_full_text(hull)
    except Exception as e:
        print(f"{hull.upper()}: fetch failed ({e}), retrying in 60s")
        time.sleep(60)
        return fetch_full_text(hull)


def check(hull: str, dry_run: bool):
    """Return a markdown section describing changes, or None if unchanged."""
    text = fetch_with_retry(hull)
    lines = text.split("\n")
    entry = find_last_entry(text)
    location = find_location(entry)
    date = extract_date(entry)
    print(f"{hull.upper()} -> {location} ({date})\n  last entry: {entry}\n  {len(lines)} lines on page")

    path = os.path.join(STATE_DIR, f"{hull.lower()}.json")
    old = None
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)

    hashes = sorted({line_hash(ln) for ln in lines})
    if old and old["last_entry"] == entry and old["line_hashes"] == hashes:
        print("  no change")
        return None

    if not dry_run:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"hull": hull.upper(), "last_entry": entry, "location": location,
                       "line_hashes": hashes}, f, indent=1)
            f.write("\n")

    where = f"{location} ({date})" if location != "Location unclear" else date
    header = f"### {hull.upper()}: {where}\n\n**Newest entry:** {entry}\n\n{page_url(hull)}\n"
    if old is None:
        print("  first check" + ("" if dry_run else ", baseline saved"))
        return header + "\n_First check: now watching this page for changes._\n"

    seen = set(old["line_hashes"])
    new_lines = [ln for ln in lines if line_hash(ln) not in seen]
    print(f"  CHANGED: {len(new_lines)} new line(s)")
    body = header
    if new_lines:
        body += "\n**New on the page:**\n\n" + "\n".join(f"> {ln}" for ln in new_lines[:MAX_NEW_LINES]) + "\n"
        if len(new_lines) > MAX_NEW_LINES:
            body += f"\n_...and {len(new_lines) - MAX_NEW_LINES} more lines._\n"
    else:
        body += "\n_Lines were removed or reordered; nothing new was added._\n"
    return body


def main(argv):
    dry_run = "--dry-run" in argv
    hulls = [a for a in argv[1:] if not a.startswith("--")]
    if not hulls:
        print(__doc__)
        return 1

    sections = [s for s in (check(hull, dry_run) for hull in hulls) if s]
    if not sections:
        return 0

    names = ", ".join(s.split(":")[0].replace("### ", "") for s in sections)
    title = f"Ship history updated: {names}"
    if all("_First check:" in s for s in sections):
        title = f"Now watching ship history: {names}"
    if dry_run:
        print(f"\n[dry run] would open issue: {title}")
        return 0
    with open(ISSUE_FILE, "w") as f:
        f.write(title + "\n" + "\n".join(sections))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
