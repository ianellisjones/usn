# Ship List & Data Sources

## Where the Data Comes From

⚠️ **Do NOT fetch uscarriers.net directly** — it blocks Claude with bot detection (403 error).

Instead, fetch these GitHub-hosted files (no blocking). They are refreshed every day by an
automated scraper that pulls from uscarriers.net using a browser header Claude can't set.

| What you want | Fetch this URL |
|---------------|----------------|
| Simple text list (default) | `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.txt` |
| Structured JSON (dates, status) | `https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.json` |
| Live tracker page (fallback) | `https://ianellisjones.github.io/usn/index.html` |

---

## The Ships (for reference)

### Aircraft Carriers (11 CVN)

| Hull | Ship Name |
|------|-----------|
| CVN68 | USS Nimitz |
| CVN69 | USS Dwight D. Eisenhower |
| CVN70 | USS Carl Vinson |
| CVN71 | USS Theodore Roosevelt |
| CVN72 | USS Abraham Lincoln |
| CVN73 | USS George Washington |
| CVN74 | USS John C. Stennis |
| CVN75 | USS Harry S. Truman |
| CVN76 | USS Ronald Reagan |
| CVN77 | USS George H.W. Bush |
| CVN78 | USS Gerald R. Ford |

### Amphibious Assault Ships (9 LHA/LHD)

| Hull | Ship Name |
|------|-----------|
| LHD1 | USS Wasp |
| LHD2 | USS Essex |
| LHD3 | USS Kearsarge |
| LHD4 | USS Boxer |
| LHD5 | USS Bataan |
| LHD7 | USS Iwo Jima |
| LHD8 | USS Makin Island |
| LHA6 | USS America |
| LHA7 | USS Tripoli |

---

## JSON Shape

`fleet_latest.json` looks like this:

```json
{
  "updated": "2026-04-12 07:03 UTC",
  "source": "http://uscarriers.net",
  "ships": [
    {
      "hull": "CVN68",
      "name": "USS Nimitz",
      "type": "CVN",
      "location": "South Pacific Ocean",
      "date": "April 2026",
      "status": "USS Nimitz transiting the South Pacific Ocean en route to Norfolk..."
    }
  ]
}
```
