# How To Read the Data

You are NOT scraping uscarriers.net yourself (it blocks Claude). You're reading a
pre-scraped file from GitHub. This is much simpler.

## The Default Path (fleet_latest.txt)

1. Fetch `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.txt`
2. It's already a clean list. Print it to the user, or lightly reformat per
   `04_OUTPUT_FORMAT.md`.

That's the whole job for a normal "run."

## The Structured Path (fleet_latest.json)

Use this when the user wants dates or full status sentences.

1. Fetch `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.json`
2. Each ship object has:
   - `hull` — e.g. `CVN68`
   - `name` — e.g. `USS Nimitz`
   - `type` — `CVN`, `LHD`, or `LHA`
   - `location` — the current location (already computed for you)
   - `date` — date of the newest entry
   - `status` — the full status sentence from uscarriers.net
3. Show `hull`, `name`, `location` by default; add `date`/`status` if asked.

## The Fallback Path (index.html)

If both raw files fail to load:

1. Fetch `https://ianellisjones.github.io/usn/index.html`
2. Find the line `const shipsData = [ ... ];`
3. It's a JSON array of ship objects, each with `hull`, `name`, and `location`.
4. Read those and build the list.

## Freshness

- Check the `updated` field (JSON) or `Updated:` header (txt) and mention it if the user
  asks how current the data is.
- The scraper runs daily at ~06:00 UTC, so data is at most ~24 hours old.

## What NOT To Do

- ❌ Don't fetch `http://uscarriers.net/...` — it returns 403 (bot blocked).
- ❌ Don't guess or invent locations. If the file is missing a ship, say so.
- ❌ Don't pull from random news sites unless the user explicitly asks for a live
   cross-check — the GitHub file is the source of truth for this project.
