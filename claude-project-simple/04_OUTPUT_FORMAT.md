# Output Format

Keep it simple. The default output is a plain list — hull, ship name, location.

## Default Output (what to show every time)

```
U.S. AIRCRAFT CARRIERS — Latest Locations

1.  CVN68  USS Nimitz                  —  San Diego
2.  CVN69  USS Dwight D. Eisenhower    —  Norfolk
3.  CVN70  USS Carl Vinson             —  San Diego
4.  CVN71  USS Theodore Roosevelt      —  Pacific Ocean
5.  CVN72  USS Abraham Lincoln         —  South China Sea
6.  CVN73  USS George Washington       —  Yokosuka
7.  CVN74  USS John C. Stennis         —  Newport News
8.  CVN75  USS Harry S. Truman         —  Mediterranean
9.  CVN76  USS Ronald Reagan           —  Bremerton
10. CVN77  USS George H.W. Bush        —  Norfolk
11. CVN78  USS Gerald R. Ford          —  Atlantic Ocean

U.S. AMPHIBIOUS ASSAULT SHIPS — Latest Locations

1.  LHD1  USS Wasp          —  Norfolk
2.  LHD2  USS Essex         —  San Diego
3.  LHD3  USS Kearsarge     —  Norfolk
4.  LHD4  USS Boxer         —  San Diego
5.  LHD5  USS Bataan        —  Norfolk
6.  LHD7  USS Iwo Jima      —  Norfolk
7.  LHD8  USS Makin Island  —  San Diego
8.  LHA6  USS America       —  Sasebo
9.  LHA7  USS Tripoli       —  San Diego
```

## Rules

- One line per ship. Hull, name, then `—` and the location.
- Carriers first, then amphibs.
- **No** dates, **no** full status sentences, **no** JSON, **no** tables — unless the
  user explicitly asks for them.
- If a ship has no recent data, write `— (no recent data)`.

## Optional Add-Ons (only if the user asks)

- **"with dates"** → add the entry date at the end: `—  Mediterranean  (Apr 8, 2026)`
- **"with details"** → add the full status sentence under each line.
- **"as a table"** → use a markdown table with Hull / Name / Location columns.
