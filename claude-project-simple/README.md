# Simple Fleet Tracker — Claude Project

A stripped-down Claude Project that reports the latest carrier and amphib locations as a
plain list.

## Important: How It Gets Data

uscarriers.net **blocks Claude from fetching it directly** (bot detection → 403). The
Python scraper in this repo works because it sends a spoofed browser header — something a
Claude Project cannot do.

So this project does NOT scrape uscarriers.net itself. Instead:

1. A GitHub Action runs `fleet_scraper.py` daily. It scrapes uscarriers.net and publishes
   a small file: **`fleet_latest.txt`** (and `fleet_latest.json`).
2. The Claude Project **fetches that published file from GitHub**, which is not blocked.

```
uscarriers.net  --(daily scrape, browser header)-->  fleet_latest.txt on GitHub
                                                              |
                                                    Claude Project fetches this
```

## What It Covers

- 11 aircraft carriers (CVN)
- 9 amphibious assault ships (LHA/LHD)

## The Files (feed all of these into the Project)

| File | Purpose |
|------|---------|
| `01_INSTRUCTIONS.md` | The super prompt — **paste into Custom Instructions** |
| `02_SHIP_LIST.md` | The data URLs + the 20 ships |
| `03_HOW_TO_READ.md` | How to read the published file |
| `04_OUTPUT_FORMAT.md` | What the output should look like |
| `05_RUN_PROMPTS.md` | Copy-paste prompts to run it |
| `USCN_LIVE_SCRAPER.md` | Live scraper: fetch each ship via a reader proxy, read the BOTTOM entry |

## Two Ways To Get Data

1. **Pre-scraped file (fast, recommended):** fetch `fleet_latest.txt` from GitHub — the
   daily Action already scraped it. See `01_INSTRUCTIONS.md`.
2. **Live scrape on demand:** drive `web_fetch` through a reader proxy to read the bottom
   entry of each uscarriers.net page yourself. See `USCN_LIVE_SCRAPER.md`. Slower, but
   bypasses the daily file and confirms a single ship live.

For a guaranteed no-truncation result outside a Project, run `../uscn_last_entry.py`
(e.g. `python uscn_last_entry.py cvn75 --carriers`).

## Setup (2 minutes)

1. Go to **claude.ai** → **Projects** → **Create Project**.
2. Name it **"Fleet Tracker (Simple)"**.
3. Paste the full contents of `01_INSTRUCTIONS.md` into **Custom Instructions**.
4. Upload the other four `.md` files as **Project Knowledge**.
5. Make sure the model has **web fetch/browsing** enabled.

## Run It

```
Run the fleet tracker. Fetch
https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.txt
and give me the simple list of all 11 carriers and 9 amphibs with their latest locations.
```

You'll get a clean list like `CVN68  USS Nimitz  —  South Pacific Ocean`.

## Data Endpoints

| File | Raw URL |
|------|---------|
| Text list | `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.txt` |
| JSON | `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.json` |
| Live page (fallback) | `https://ianellisjones.github.io/usn/index.html` |

> Note: these URLs point to the `main` branch. The `fleet_latest.*` files land on `main`
> once this branch is merged and the daily scraper runs (or immediately, since seed
> versions are committed).

## Note

The full-featured project (coordinates, JSON export for the globe, 77 destroyers) lives in
the `../claude-project/` folder.
