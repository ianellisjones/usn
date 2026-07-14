# USCN Live Scraper — Bottom-of-Page Last Location

This is the "scraper" you run inside a Claude Project. It does NOT run Python — a Project
has no networked code sandbox. It works by driving the **web_fetch** tool through a
**reader proxy**, then reading the **last entry at the bottom** of the page.

Two problems it solves:
- **Bot block (403):** uscarriers.net rejects Claude's direct fetch. The reader proxy
  fetches the page server-side with a real browser header, so it comes back clean.
- **Truncation:** the newest entry is at the very BOTTOM. This procedure fetches the full
  text and explicitly extracts only the final dated entry, so a long history can't push the
  answer out of view.

---

## The Fetch Method (do this for each ship)

Fetch the ship's page **through the reader proxy** by prefixing the uscarriers URL with
`https://r.jina.ai/`:

```
https://r.jina.ai/http://uscarriers.net/cvn68history.htm
```

Pattern:
```
https://r.jina.ai/http://uscarriers.net/<page>
  carriers:  cvn68history.htm ... cvn78history.htm
  amphibs:   lhd1history.htm, lha6history.htm, etc.
```

**Extraction prompt to use with web_fetch (paste as the fetch instruction):**

> This page is a chronological log of a Navy ship's movements, OLDEST at the top and
> NEWEST at the very bottom. Read all the way to the END of the document. Return ONLY the
> final (bottom-most) dated status entry, verbatim, including its date. Ignore everything
> above it. Then, on a second line, state the ship's CURRENT location — which is the LAST
> place named in that final entry.

---

## Turning the Last Entry Into a Location

The current location is the **last place mentioned** in that bottom entry (ships move, so
the rightmost place is where they are now).

| Bottom entry says… | Location |
|--------------------|----------|
| "moored at Naval Station Norfolk" | Norfolk |
| "arrived at Naval Base San Diego" | San Diego |
| "moored at Fleet Activities Yokosuka" | Yokosuka |
| "operating in the South China Sea" | South China Sea |
| "underway in the Mediterranean" | Mediterranean |
| "transited the Suez Canal into the Red Sea" | Red Sea |

**"Departed" with no new place named → the ship is at sea off that coast:**
- departed San Diego / Pearl Harbor / Bremerton → Pacific Ocean
- departed Norfolk / Mayport → Atlantic Ocean
- departed Yokosuka / Sasebo → Western Pacific

---

## Fallback Order (if the proxy fails)

1. `https://r.jina.ai/http://uscarriers.net/<page>`  ← try first
2. `https://api.allorigins.win/raw?url=http://uscarriers.net/<page>`  ← alt proxy
3. Direct `http://uscarriers.net/<page>`  ← usually 403, last resort

If a page still won't load after all three, output `— (page unavailable)` for that ship
and continue to the next. Never stop the whole run over one ship.

If the returned text looks cut off *before* any 2025/2026 entry, re-fetch the same proxy
URL and ask specifically for "the final 1500 characters / the very end of the document."

---

## READY PROMPTS

### One ship (fast, most reliable)

```
Act as the USCN Live Scraper (see USCN_LIVE_SCRAPER.md).
Fetch https://r.jina.ai/http://uscarriers.net/cvn75history.htm
Read to the BOTTOM, return the final dated entry verbatim, and tell me CVN75's
current location (the last place named in that entry).
```

### All 11 carriers

```
Act as the USCN Live Scraper (see USCN_LIVE_SCRAPER.md). For each carrier below,
fetch https://r.jina.ai/http://uscarriers.net/<page>, read the BOTTOM entry, and give me
the current location. Output a simple list: hull, name, location.

cvn68history.htm  CVN68 USS Nimitz
cvn69history.htm  CVN69 USS Dwight D. Eisenhower
cvn70history.htm  CVN70 USS Carl Vinson
cvn71history.htm  CVN71 USS Theodore Roosevelt
cvn72history.htm  CVN72 USS Abraham Lincoln
cvn73history.htm  CVN73 USS George Washington
cvn74history.htm  CVN74 USS John C. Stennis
cvn75history.htm  CVN75 USS Harry S. Truman
cvn76history.htm  CVN76 USS Ronald Reagan
cvn77history.htm  CVN77 USS George H.W. Bush
cvn78history.htm  CVN78 USS Gerald R. Ford
```

### All 9 amphibs

```
Act as the USCN Live Scraper (see USCN_LIVE_SCRAPER.md). For each amphib below,
fetch https://r.jina.ai/http://uscarriers.net/<page>, read the BOTTOM entry, and give me
the current location as a simple list.

lhd1history.htm  LHD1 USS Wasp
lhd2history.htm  LHD2 USS Essex
lhd3history.htm  LHD3 USS Kearsarge
lhd4history.htm  LHD4 USS Boxer
lhd5history.htm  LHD5 USS Bataan
lhd7history.htm  LHD7 USS Iwo Jima
lhd8history.htm  LHD8 USS Makin Island
lha6history.htm  LHA6 USS America
lha7history.htm  LHA7 USS Tripoli
```

---

## Notes / Limits

- The reader proxy (r.jina.ai) is a free public service. On-demand single/looped fetches
  are fine; very heavy use may rate-limit — if so, wait a moment and retry, or use the
  allorigins fallback.
- Fetching 20 ships one-by-one is slower than reading the pre-scraped `fleet_latest.txt`
  file. Use this live scraper when you want to confirm a single ship or bypass the daily
  file entirely.
- For a guaranteed no-truncation result, run the Python script `uscn_last_entry.py`
  (in the repo root) anywhere with real network — it prints the exact bottom entry.
