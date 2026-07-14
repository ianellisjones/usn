# Example Outputs Reference

Sample outputs showing the expected format when running the Fleet Tracker prompts.

## Location Table Format

When asked to "run" or "update" a tracker, output a markdown table with these columns:

### Carrier/Amphib Table Example

```
| Hull | Ship Name | Location | Date | Status |
|------|-----------|----------|------|--------|
| CVN68 | USS Nimitz | South Pacific Ocean | April 2026 | USS Nimitz transiting the South Pacific returning from a deployment to the Western Pacific. |
| CVN69 | USS Dwight D. Eisenhower | Norfolk / Portsmouth | April 2026 | USS Dwight D. Eisenhower moored at Naval Station Norfolk following extensive maintenance. |
| CVN70 | USS Carl Vinson | San Diego | April 2026 | USS Carl Vinson arrived at Naval Base San Diego on April 8. |
| CVN71 | USS Theodore Roosevelt | Pacific Ocean | April 2026 | USS Theodore Roosevelt conducting carrier qualifications in the Pacific. |
| CVN72 | USS Abraham Lincoln | South China Sea | April 2026 | USS Abraham Lincoln operating in the South China Sea with Carrier Strike Group 3. |
| CVN73 | USS George Washington | Yokosuka | April 2026 | USS George Washington moored at Fleet Activities Yokosuka, forward-deployed to Japan. |
| CVN74 | USS John C. Stennis | Norfolk / Portsmouth | April 2026 | USS John C. Stennis at Norfolk Naval Shipyard undergoing RCOH (refueling complex overhaul). |
| CVN75 | USS Harry S. Truman | Mediterranean | April 2026 | USS Harry S. Truman underway in the Mediterranean Sea conducting flight operations. |
| CVN76 | USS Ronald Reagan | Bremerton / Kitsap | April 2026 | USS Ronald Reagan at Puget Sound Naval Shipyard for scheduled maintenance. |
| CVN77 | USS George H.W. Bush | Norfolk / Portsmouth | April 2026 | USS George H.W. Bush moored at Pier 12, Naval Station Norfolk. |
| CVN78 | USS Gerald R. Ford | Atlantic Ocean | April 2026 | USS Gerald R. Ford underway in the Atlantic Ocean conducting carrier strike group exercises. |
```

### Destroyer Table Example

```
| Hull | Ship Name | Flight | Location | Date | Status |
|------|-----------|--------|----------|------|--------|
| DDG51 | USS Arleigh Burke | I | Norfolk / Portsmouth | April 2026 | USS Arleigh Burke moored at Naval Station Norfolk. |
| DDG52 | USS Barry | I | Yokosuka | April 2026 | USS Barry forward-deployed to Yokosuka, Japan. |
| DDG56 | USS John S. McCain | I | South China Sea | April 2026 | USS John S. McCain conducting freedom of navigation operations in the South China Sea. |
| DDG87 | USS Mason | IIA | Red Sea | April 2026 | USS Mason operating in the Red Sea providing escort and air defense. |
| DDG1000 | USS Zumwalt | Zumwalt | San Diego | April 2026 | USS Zumwalt moored at Naval Base San Diego. |
```

## JSON Data Format

For updating the HTML tracker files, provide JSON in this format:

### Single Ship JSON

```json
{
  "hull": "CVN68",
  "name": "USS Nimitz",
  "ship_class": "Nimitz",
  "ship_type": "CVN",
  "location": "South Pacific Ocean",
  "lat": -15.0,
  "lon": -150.0,
  "region": "PACIFIC",
  "date": "April 2026",
  "status": "USS Nimitz transiting the South Pacific returning from a deployment to the Western Pacific.",
  "source_url": "http://uscarriers.net/cvn68history.htm"
}
```

### Full shipsData Array (for index.html)

```json
const shipsData = [
  {
    "hull": "CVN68",
    "name": "USS Nimitz",
    "ship_class": "Nimitz",
    "ship_type": "CVN",
    "location": "South Pacific Ocean",
    "lat": -15.0,
    "lon": -150.0,
    "region": "PACIFIC",
    "date": "April 2026",
    "status": "USS Nimitz transiting the South Pacific."
  },
  {
    "hull": "CVN69",
    "name": "USS Dwight D. Eisenhower",
    "ship_class": "Nimitz",
    "ship_type": "CVN",
    "location": "Norfolk / Portsmouth",
    "lat": 36.9473,
    "lon": -76.3134,
    "region": "CONUS",
    "date": "April 2026",
    "status": "USS Eisenhower moored at Naval Station Norfolk."
  }
  // ... continue for all ships
];
```

### Destroyer JSON (for destroyers.html)

```json
{
  "hull": "DDG87",
  "name": "USS Mason",
  "ship_class": "Arleigh Burke",
  "flight": "IIA",
  "location": "Red Sea",
  "lat": 20.0,
  "lon": 38.0,
  "region": "CENTCOM",
  "date": "April 2026",
  "status": "USS Mason operating in the Red Sea.",
  "source_url": "http://uscarriers.net/ddg87history.htm"
}
```

## Fleet Summary Format

When providing a fleet overview:

```
## U.S. Navy Fleet Status Summary - April 2026

### Aircraft Carriers (11 CVN)
- **Deployed**: 3 (CVN72 SCS, CVN75 MED, CVN78 LANT)
- **In Port**: 6 (CVN69, CVN70, CVN73, CVN74, CVN77 NORFOLK; CVN76 BREMERTON)
- **Transiting**: 2 (CVN68 returning PACFLT, CVN71 QUALOPS)

### Amphibious Assault Ships (9 LHA/LHD)
- **Deployed**: 4
- **In Port**: 5

### Destroyers (77 DDG)
- **CONUS**: 45
- **WESTPAC**: 15
- **CENTCOM**: 12
- **EUCOM**: 5

### Regional Distribution
| Region | CVN | LHA/LHD | DDG | Total |
|--------|-----|---------|-----|-------|
| Atlantic | 3 | 2 | 25 | 30 |
| Pacific | 4 | 3 | 30 | 37 |
| WESTPAC | 1 | 2 | 15 | 18 |
| CENTCOM | 0 | 1 | 5 | 6 |
| EUCOM | 1 | 1 | 2 | 4 |
```

## Status Entry Parsing Examples

### Example 1: Ship in Port

**Raw text from uscarriers.net:**
> April 8, 2026 - USS Carl Vinson arrived at Naval Base San Diego following deployment.

**Parsed output:**
- Location: `San Diego`
- Date: `April 8, 2026` or `April 2026`
- Status: Full sentence as shown

### Example 2: Ship Underway

**Raw text:**
> April 2026 - USS Mason conducting Red Sea operations with CSG-8.

**Parsed output:**
- Location: `Red Sea`
- Date: `April 2026`
- Status: Full sentence

### Example 3: Departed (Underway)

**Raw text:**
> March 28, 2026 - USS Theodore Roosevelt departed San Diego for the Western Pacific.

**Parsed output:**
- Location: `Western Pacific (WESTPAC)` (NOT San Diego - ship departed)
- Date: `March 2026`
- Status: Full sentence

### Example 4: Multiple Locations (Use LAST)

**Raw text:**
> April 2026 - USS Lincoln departed Pearl Harbor, transited through Guam, and is now operating in the South China Sea.

**Parsed output:**
- Location: `South China Sea` (rightmost location = current)
- Date: `April 2026`
- Status: Full sentence
