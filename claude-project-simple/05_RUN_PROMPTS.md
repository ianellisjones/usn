# Run Prompts — Copy & Paste

Ready-to-use prompts. Paste one into the project chat to run it.

## Main Command — Run Everything

```
Run the fleet tracker. Fetch
https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.txt
and give me the simple list of all 11 carriers and 9 amphibs with their latest locations.
```

## Carriers Only

```
Run the carriers. Fetch fleet_latest.txt from GitHub and show me just the 11 CVNs
and their latest locations.
```

## Amphibs Only

```
Run the amphibs. Fetch fleet_latest.txt from GitHub and show me just the 9 LHA/LHDs
and their latest locations.
```

## One Ship

```
Where is CVN75 USS Truman right now? Fetch
https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.json
and tell me its location and status.
```

## With Dates / Full Status

```
Run the fleet tracker with details. Fetch
https://raw.githubusercontent.com/ianellisjones/usn/main/fleet_latest.json
and for each ship give the location plus the date and full status sentence.
```

## How Fresh Is the Data?

```
Fetch fleet_latest.json from GitHub and tell me the "updated" timestamp so I know
how current this is.
```

---

## Why These Use GitHub, Not uscarriers.net

uscarriers.net blocks Claude's fetch (bot detection → 403). A script on GitHub scrapes it
daily with a browser header and publishes the results to `fleet_latest.txt` / `.json`,
which Claude CAN fetch. You always read the fresh published file — no blocking, no guessing.
