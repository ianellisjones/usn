# Quick Commands Reference

Copy-paste prompts to run the Fleet Tracker in Claude Projects.

## Primary Commands

### Update All Carriers

```
Run the carrier tracker. Fetch the latest locations for all 11 CVNs from uscarriers.net:
- CVN68 through CVN78

Output a markdown table with Hull, Ship Name, Location, Date, and full Status.
Then provide the JSON data to update index.html.
```

### Update All Amphibs

```
Run the amphib tracker. Fetch the latest locations for all 9 LHA/LHDs from uscarriers.net:
- LHD1, LHD2, LHD3, LHD4, LHD5, LHD7, LHD8
- LHA6, LHA7

Output a markdown table with Hull, Ship Name, Location, Date, and full Status.
Then provide the JSON data to update index.html.
```

### Update All Destroyers

```
Run the destroyer tracker. Fetch the latest locations for all 77 DDGs from uscarriers.net:
- DDG51-DDG71 (Flight I)
- DDG72-DDG78 (Flight II)
- DDG79-DDG121 (Flight IIA)
- DDG122, DDG123, DDG125 (Flight III)
- DDG1000, DDG1001, DDG1002 (Zumwalt)

Output a markdown table with Hull, Ship Name, Flight, Location, Date, and full Status.
Then provide the JSON data to update destroyers.html.
```

### Update Carriers + Amphibs Combined

```
Run the fleet tracker. Fetch latest locations from uscarriers.net for:
- All 11 aircraft carriers (CVN68-CVN78)
- All 9 amphibious assault ships (LHD1-8, LHA6-7)

Output a combined markdown table and provide the JSON for index.html.
```

## Single Ship Lookups

### Check Specific Carrier

```
What is the current location of CVN68 (USS Nimitz)?
Fetch from http://uscarriers.net/cvn68history.htm
```

### Check Specific Destroyer

```
What is the current location of DDG87 (USS Mason)?
Fetch from http://uscarriers.net/ddg87history.htm
```

### Check Multiple Ships

```
Check the current locations of these ships:
- CVN75 USS Harry S. Truman
- DDG87 USS Mason
- DDG55 USS Stout

Fetch each from uscarriers.net and provide status.
```

## Regional Queries

### Ships in the Red Sea

```
Which U.S. Navy surface combatants are currently operating in the Red Sea?
Check CVNs, LHDs, and key DDGs from uscarriers.net.
```

### Ships in WESTPAC

```
List all U.S. Navy ships currently in the Western Pacific:
- Forward-deployed ships in Yokosuka/Sasebo
- Ships transiting or operating in WESTPAC

Check uscarriers.net for current positions.
```

### Ships Deployed to CENTCOM

```
What carriers and destroyers are currently deployed to the CENTCOM AOR?
Check for ships in the Persian Gulf, Arabian Sea, Gulf of Aden, and Red Sea.
```

## Fleet Posture Summaries

### Full Fleet Summary

```
Provide a U.S. Navy fleet posture summary:
1. How many carriers are deployed vs. in port?
2. How many amphibs are deployed?
3. Regional distribution of surface combatants

Use latest data from uscarriers.net.
```

### Carrier Strike Group Lookup

```
Which carrier strike groups are currently deployed?
For each deployed CVN, identify:
- Location
- Likely accompanying DDGs
- Mission area (CENTCOM, EUCOM, WESTPAC)
```

## Data Export Commands

### Export for index.html

```
Generate the complete shipsData JavaScript array for index.html with:
- All 11 carriers
- All 9 amphibs
- Current coordinates from LOCATION_COORDS
- Latest status from uscarriers.net

Format as: const shipsData = [...];
```

### Export for destroyers.html

```
Generate the complete shipsData JavaScript array for destroyers.html with:
- All 77 destroyers
- Current coordinates with clustering offsets
- Flight designations (I, II, IIA, III, Zumwalt)
- Latest status from uscarriers.net

Format as: const shipsData = [...];
```

## Manual Location Updates

### Quick Carrier Update (No Scrape)

```
Update these carrier locations in index.html (no scraping needed):

CVN68 USS Nimitz - South Pacific Ocean, returning home
CVN69 USS Eisenhower - Norfolk, maintenance
CVN70 USS Carl Vinson - San Diego, in port
CVN71 USS Roosevelt - Pacific, underway
CVN72 USS Lincoln - South China Sea, deployed
CVN73 USS Washington - Yokosuka, homeport
CVN74 USS Stennis - Norfolk, RCOH
CVN75 USS Truman - Mediterranean, deployed
CVN76 USS Reagan - Bremerton, maintenance
CVN77 USS Bush - Norfolk, in port
CVN78 USS Ford - Atlantic, training

Generate the JSON shipsData array.
```

## Tips for Best Results

1. **Be specific** - Name exact ships or hull numbers when possible
2. **Specify output** - Request "markdown table" or "JSON for HTML"
3. **Include all ships** - For full updates, list all hull numbers
4. **Date awareness** - System prioritizes 2025/2026/2027 status entries
5. **Location priority** - Last mentioned location = current position
