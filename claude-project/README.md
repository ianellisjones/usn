# U.S. Navy Fleet Tracker - Claude Project Setup

This folder contains all the files needed to create a Claude Project that can pull ship locations from uscarriers.net on demand.

## Quick Setup

1. Go to [claude.ai](https://claude.ai) and create a new Project
2. Name it "U.S. Navy Fleet Tracker"
3. Upload these files as Project Knowledge:
   - `SYSTEM_PROMPT.md` - **Set this as the Project Instructions** (Custom Instructions)
   - `SHIP_DATABASE.md` - Complete list of all ships with URLs
   - `COORDINATES.md` - Location coordinate reference
   - `EXAMPLE_OUTPUTS.md` - Sample output formats
   - `QUICK_COMMANDS.md` - Ready-to-use prompts

## Project Structure

```
claude-project/
├── README.md              # This file
├── SYSTEM_PROMPT.md       # Main system prompt (use as Custom Instructions)
├── SHIP_DATABASE.md       # 97 ships: 11 CVN, 9 LHA/LHD, 77 DDG
├── COORDINATES.md         # 30+ locations with lat/lon
├── EXAMPLE_OUTPUTS.md     # Table and JSON format examples
└── QUICK_COMMANDS.md      # Copy-paste prompts
```

## How to Use

### Option 1: Upload as Project Knowledge
1. Create new Claude Project
2. Copy contents of `SYSTEM_PROMPT.md` into Custom Instructions
3. Upload remaining 4 files as Knowledge documents

### Option 2: Paste as Context
Simply paste the full system prompt into a conversation and add the ship database tables as needed.

## Sample Prompts

Once set up, you can use prompts like:

- "Update the carrier tracker" - Scrapes all 11 CVNs
- "Update the destroyer tracker" - Scrapes all 77 DDGs
- "Where is CVN75 USS Truman?" - Single ship lookup
- "What ships are in the Red Sea?" - Regional query

## What the Project Does

1. **Fetches** ship history pages from uscarriers.net
2. **Parses** the most recent status entry (2025/2026)
3. **Extracts** current location using keyword matching
4. **Outputs** formatted markdown tables
5. **Generates** JSON data for updating tracker HTML files

## Limitations

- Cannot actually scrape websites (use manual copy-paste for status text)
- Submarine data is classified (not available on uscarriers.net)
- Status text may be outdated by days/weeks

## Integration with GitHub Repository

The Claude Project complements the automated scrapers:

| Component | Runs | Updates |
|-----------|------|---------|
| `fleet_scraper.py` | Daily 6 AM UTC | index.html |
| `destroyer_scraper.py` | Daily 7 AM UTC | destroyers.html |
| Claude Project | On-demand | Manual updates |

Use the Claude Project for:
- Quick status checks
- Verifying scraper output
- Manual updates when scrapers fail
- Ad-hoc queries about fleet disposition
