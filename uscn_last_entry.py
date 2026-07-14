#!/usr/bin/env python3
"""
USCN Last-Entry Scraper
=======================

Fetches a single ship's history page from uscarriers.net, reads the FULL page
(no truncation), finds the LAST/bottom-most status entry, and prints that entry
plus the ship's current location (the last place named in it).

This is the guaranteed-correct, no-truncation companion to the Claude Project
"live scraper" (claude-project-simple/USCN_LIVE_SCRAPER.md). It needs real
network access with a browser User-Agent, so run it anywhere Python + requests
work (Claude Code, your laptop, Colab, Replit, a GitHub Action) — NOT inside a
claude.ai Project, which has no networked code sandbox.

Usage:
    python uscn_last_entry.py cvn75
    python uscn_last_entry.py CVN75
    python uscn_last_entry.py ddg87
    python uscn_last_entry.py cvn68 cvn70 lha6      # several at once
    python uscn_last_entry.py --carriers            # all 11 CVNs
    python uscn_last_entry.py --amphibs             # all 9 LHA/LHDs

Created for @ianellisjones / IEJ Media.
"""

import re
import sys

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CARRIERS = ["cvn68", "cvn69", "cvn70", "cvn71", "cvn72", "cvn73",
            "cvn74", "cvn75", "cvn76", "cvn77", "cvn78"]
AMPHIBS = ["lhd1", "lhd2", "lhd3", "lhd4", "lhd5", "lhd7", "lhd8", "lha6", "lha7"]

# Location keywords, most specific first. The CURRENT location is the LAST
# (rightmost) of these that appears in the newest entry.
LOCATION_KEYWORDS = [
    ("Rota", ["rota"]),
    ("Okinawa", ["okinawa", "white beach"]),
    ("Sasebo", ["sasebo"]),
    ("Yokosuka", ["yokosuka"]),
    ("Norfolk", ["norfolk", "portsmouth", "naval station norfolk"]),
    ("San Diego", ["san diego", "north island", "coronado"]),
    ("Bremerton / Kitsap", ["bremerton", "kitsap", "puget sound"]),
    ("Newport News", ["newport news", "huntington ingalls"]),
    ("Pearl Harbor", ["pearl harbor"]),
    ("Mayport", ["mayport"]),
    ("Everett", ["everett"]),
    ("Pascagoula", ["pascagoula", "ingalls"]),
    ("Guam", ["guam", "apra"]),
    ("Singapore", ["singapore", "changi"]),
    ("Bahrain", ["bahrain", "manama"]),
    ("Dubai", ["dubai", "jebel ali"]),
    ("Busan", ["busan"]),
    ("Ponce, Puerto Rico", ["ponce"]),
    ("Caribbean Sea", ["caribbean", "puerto rico", "st. croix", "virgin islands"]),
    ("South China Sea", ["south china sea", "luzon", "bashi channel"]),
    ("Philippine Sea", ["philippine sea"]),
    ("East China Sea", ["east china sea"]),
    ("Sea of Japan", ["sea of japan"]),
    ("Western Pacific", ["western pacific", "westpac"]),
    ("Red Sea", ["red sea"]),
    ("Persian Gulf", ["persian gulf", "arabian gulf"]),
    ("Gulf of Oman", ["gulf of oman"]),
    ("Gulf of Aden", ["gulf of aden"]),
    ("Arabian Sea", ["arabian sea"]),
    ("Mediterranean", ["mediterranean", "med sea"]),
    ("Baltic Sea", ["baltic"]),
    ("Black Sea", ["black sea"]),
    ("North Sea", ["north sea"]),
    ("Norwegian Sea", ["norwegian sea"]),
    ("Strait of Gibraltar", ["gibraltar"]),
    ("Suez Canal", ["suez"]),
    ("Atlantic Ocean", ["atlantic"]),
    ("Pacific Ocean", ["pacific"]),
    ("Indian Ocean", ["indian ocean"]),
]

# "departed X" with no later place named => at sea off that coast.
DEPARTURE = [
    ("departed san diego", "Pacific Ocean"),
    ("departed pearl harbor", "Pacific Ocean"),
    ("departed bremerton", "Pacific Ocean"),
    ("departed everett", "Pacific Ocean"),
    ("departed norfolk", "Atlantic Ocean"),
    ("departed mayport", "Atlantic Ocean"),
    ("departed yokosuka", "Western Pacific"),
    ("departed sasebo", "Western Pacific"),
    ("departed rota", "Mediterranean"),
]

STATUS_KEYWORDS = [
    "moored", "anchored", "underway", "arrived", "departed", "transited",
    "operations", "returned", "participated", "conducted", "moved", "visited",
    "pulled into", "sea trials", "deployed", "port call", "homeport",
]


def fetch_full_text(hull: str) -> str:
    """Fetch the ENTIRE page as clean text (no truncation)."""
    import requests
    from bs4 import BeautifulSoup

    url = f"http://uscarriers.net/{hull.lower()}history.htm"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    return "\n".join(lines)


def find_last_entry(text: str) -> str:
    """Return the bottom-most status entry, preferring 2025-2027, then 2024."""
    lines = text.split("\n")

    # Track the running year as we descend the page.
    processed = []
    running_year = "Unknown"
    for line in lines:
        m = re.match(r"^(20\d\d)", line)
        if m:
            running_year = m.group(1)
        processed.append((running_year, line))

    for allowed in (("2027", "2026", "2025"), ("2024",), None):
        for year, line in reversed(processed):
            low = line.lower()
            if allowed is not None and year not in allowed:
                continue
            if any(k in low for k in STATUS_KEYWORDS):
                if low.startswith("from ") and " - " in low:
                    continue
                return line
    return "No datable status entry found."


def find_location(entry: str) -> str:
    """The current location = the LAST place named in the entry."""
    low = entry.lower()

    # Departure override only if nothing is named after "departed X".
    for phrase, loc in DEPARTURE:
        if phrase in low:
            after = low[low.rfind(phrase) + len(phrase):]
            if not any(kw in after for _, kws in LOCATION_KEYWORDS for kw in kws):
                return loc

    best_loc, best_pos = None, -1
    for loc, kws in LOCATION_KEYWORDS:
        for kw in kws:
            pos = low.rfind(kw)
            if pos > best_pos:
                best_pos, best_loc = pos, loc
    return best_loc or "Location unclear"


def extract_date(entry: str) -> str:
    months = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}"
    m = re.findall(months, entry, re.IGNORECASE)
    if m:
        return m[-1]
    y = re.findall(r"20\d\d", entry)
    return y[-1] if y else "date n/a"


def scrape(hull: str) -> None:
    try:
        text = fetch_full_text(hull)
    except Exception as e:
        print(f"{hull.upper():<8} ERROR: {e}")
        return
    entry = find_last_entry(text)
    location = find_location(entry)
    date = extract_date(entry)
    print(f"{hull.upper():<8} -> {location}  ({date})")
    print(f"         last entry: {entry}")
    print()


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__)
        return 1

    hulls = []
    for a in args:
        if a in ("--carriers", "-c"):
            hulls += CARRIERS
        elif a in ("--amphibs", "-a"):
            hulls += AMPHIBS
        elif a in ("--all",):
            hulls += CARRIERS + AMPHIBS
        else:
            hulls.append(a)

    for hull in hulls:
        scrape(hull)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
