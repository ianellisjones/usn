#!/usr/bin/env python3
"""
Watch https://www.navy.mil/Press-Office/ and alert the moment a new article appears.

Usage:
    python3 navy_press_monitor.py                  # check every 30s
    python3 navy_press_monitor.py -i 15            # check every 15s
    python3 navy_press_monitor.py -k aircraft F/A-XX   # extra-loud alert on keywords
    python3 navy_press_monitor.py --no-open        # don't auto-open new articles

Standard library only - no pip install needed.
"""
import argparse
import hashlib
import html
import re
import subprocess
import sys
import time
import urllib.request
import webbrowser
from datetime import datetime

URL = "https://www.navy.mil/Press-Office/"
BASE = "https://www.navy.mil"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
# Article links on navy.mil look like /Press-Office/News-Stories/Article/4312345/some-title/
ARTICLE_RE = re.compile(r'<a[^>]+href="([^"]*/Article/\d+[^"]*)"[^>]*>(.*?)</a>', re.I | re.S)


def fetch():
    # cache-buster so we never get a stale CDN copy
    req = urllib.request.Request(f"{URL}?_={int(time.time())}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def clean(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def articles(page):
    """Return {url: title} for every article link on the page."""
    found = {}
    for href, text in ARTICLE_RE.findall(page):
        url = href if href.startswith("http") else BASE + href
        title = clean(text)
        if title and len(title) > len(found.get(url, "")):
            found[url] = title
        else:
            found.setdefault(url, title or url.rstrip("/").rsplit("/", 1)[-1].replace("-", " "))
    return found


def text_hash(page):
    """Fallback fingerprint of visible text if no article links are found."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.I | re.S)
    return hashlib.sha256(clean(body).encode()).hexdigest()


def alert(title, msg):
    print("\a" * 3, end="", flush=True)  # terminal bell
    try:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            f'display notification {msg!r} with title {title!r} sound name "Glass"'],
                           timeout=5)
            subprocess.Popen(["say", title])
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", "-u", "critical", title, msg], timeout=5)
        elif sys.platform == "win32":
            import winsound
            for _ in range(3):
                winsound.Beep(1500, 300)
    except Exception:
        pass


def now():
    return datetime.now().strftime("%H:%M:%S")


def main():
    ap = argparse.ArgumentParser(description="Monitor navy.mil Press Office for new posts")
    ap.add_argument("-i", "--interval", type=int, default=30, help="seconds between checks (default 30)")
    ap.add_argument("-k", "--keywords", nargs="*", default=["aircraft", "F/A-XX", "fighter", "6th gen", "sixth"],
                    help="keywords that trigger a louder alert")
    ap.add_argument("--no-open", action="store_true", help="don't open new articles in the browser")
    args = ap.parse_args()
    kws = [k.lower() for k in args.keywords]

    print(f"[{now()}] Watching {URL} every {args.interval}s  (Ctrl+C to stop)")
    seen, fingerprint = None, None
    while True:
        try:
            page = fetch()
            arts = articles(page)
            if seen is None:
                seen, fingerprint = set(arts), text_hash(page)
                print(f"[{now()}] Baseline: {len(arts)} articles. Latest:")
                for url, t in list(arts.items())[:5]:
                    print(f"    - {t}")
                if not arts:
                    print("    (no article links parsed - falling back to whole-page change detection)")
            else:
                new = {u: t for u, t in arts.items() if u not in seen}
                if new:
                    print("\n" + "=" * 70)
                    print(f"[{now()}] *** {len(new)} NEW POST(S) ***")
                    for url, t in new.items():
                        hit = any(k in t.lower() for k in kws)
                        print(f"  {'>>> KEYWORD MATCH <<< ' if hit else ''}{t}\n    {url}")
                    print("=" * 70 + "\n")
                    first_t = next(iter(new.values()))
                    alert("NAVY: NEW PRESS RELEASE", first_t)
                    if not args.no_open:
                        for url in list(new)[:3]:
                            webbrowser.open(url)
                    seen |= set(new)
                elif not arts:
                    fp = text_hash(page)
                    if fp != fingerprint:
                        print(f"\n[{now()}] *** PAGE CHANGED *** {URL}\n")
                        alert("NAVY: Press Office page changed", URL)
                        if not args.no_open:
                            webbrowser.open(URL)
                        fingerprint = fp
                    else:
                        print(f"[{now()}] no change")
                else:
                    print(f"[{now()}] no change ({len(arts)} articles)")
                seen |= set(arts)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[{now()}] fetch error: {e}  (will retry)")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
