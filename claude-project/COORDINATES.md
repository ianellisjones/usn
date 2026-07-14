# Coordinate Reference Database

Complete coordinates for all tracked locations in the Navy Fleet Tracker.

## U.S. Ports / Shipyards

| Location | Latitude | Longitude | Region |
|----------|----------|-----------|--------|
| Norfolk / Portsmouth | 36.9473 | -76.3134 | CONUS |
| San Diego | 32.7157 | -117.1611 | CONUS |
| Bremerton / Kitsap | 47.5673 | -122.6329 | CONUS |
| Newport News | 36.9788 | -76.4280 | CONUS |
| Pearl Harbor | 21.3545 | -157.9698 | PACIFIC |
| Mayport | 30.3918 | -81.4285 | CONUS |
| Everett | 47.9790 | -122.2021 | CONUS |
| Pascagoula | 30.3658 | -88.5561 | CONUS |
| Bath | 43.9106 | -69.8206 | CONUS |

## Forward Deployed / Foreign Ports

| Location | Latitude | Longitude | Region |
|----------|----------|-----------|--------|
| Yokosuka | 35.2831 | 139.6703 | WESTPAC |
| Sasebo | 33.1595 | 129.7235 | WESTPAC |
| Guam | 13.4443 | 144.7937 | WESTPAC |
| Singapore | 1.2655 | 103.8200 | INDOPAC |
| Bahrain | 26.2235 | 50.5876 | CENTCOM |
| Dubai | 25.2582 | 55.3047 | CENTCOM |
| Busan | 35.1028 | 129.0403 | WESTPAC |
| Philippines | 14.5995 | 120.9842 | WESTPAC |
| Malaysia | 3.1390 | 101.6869 | INDOPAC |
| Okinawa | 26.3344 | 127.8056 | WESTPAC |
| Rota | 36.6175 | -6.3497 | EUCOM |
| Ponce | 17.9800 | -66.6141 | SOUTHCOM |

## Strategic Seas / Regions

| Location | Latitude | Longitude | Region |
|----------|----------|-----------|--------|
| South China Sea | 12.0000 | 114.0000 | WESTPAC |
| Western Pacific (WESTPAC) | 15.0000 | 135.0000 | WESTPAC |
| Philippine Sea | 20.0000 | 130.0000 | WESTPAC |
| East China Sea | 28.0000 | 125.0000 | WESTPAC |
| Sea of Japan | 40.0000 | 135.0000 | WESTPAC |
| Red Sea | 20.0000 | 38.0000 | CENTCOM |
| Persian Gulf | 27.0000 | 51.0000 | CENTCOM |
| Gulf of Oman | 24.5000 | 58.5000 | CENTCOM |
| Gulf of Aden | 12.5000 | 47.0000 | CENTCOM |
| Arabian Sea | 15.0000 | 65.0000 | CENTCOM |
| Mediterranean | 35.0000 | 18.0000 | EUCOM |
| Caribbean Sea | 15.5000 | -73.0000 | SOUTHCOM |
| North Sea | 56.0000 | 3.0000 | EUCOM |
| Norwegian Sea | 68.0000 | 5.0000 | EUCOM |
| Baltic Sea | 55.0000 | 15.0000 | EUCOM |
| Black Sea | 43.0000 | 35.0000 | EUCOM |

## Chokepoints / Straits

| Location | Latitude | Longitude | Region |
|----------|----------|-----------|--------|
| Strait of Gibraltar | 35.9500 | -5.6000 | EUCOM |
| Suez Canal | 30.6000 | 32.3300 | CENTCOM |
| Bab el-Mandeb | 12.5833 | 43.3333 | CENTCOM |

## Oceans (Default Positions)

| Location | Latitude | Longitude | Region |
|----------|----------|-----------|--------|
| Atlantic Ocean | 32.0000 | -65.0000 | ATLANTIC |
| Pacific Ocean | 25.0000 | -140.0000 | PACIFIC |
| Indian Ocean | -5.0000 | 75.0000 | INDOPAC |

## Region Codes

| Code | Description |
|------|-------------|
| CONUS | Continental United States |
| PACIFIC | Central/Eastern Pacific Ocean |
| ATLANTIC | Atlantic Ocean |
| WESTPAC | Western Pacific (Japan, Korea, Philippines) |
| INDOPAC | Indo-Pacific (Singapore, Malaysia, Indonesia) |
| CENTCOM | Central Command (Middle East, Persian Gulf) |
| EUCOM | European Command (Mediterranean, Europe) |
| SOUTHCOM | Southern Command (Caribbean, South America) |

## JSON Format for Code

```json
{
  "Norfolk / Portsmouth": {"lat": 36.9473, "lon": -76.3134, "region": "CONUS"},
  "San Diego": {"lat": 32.7157, "lon": -117.1611, "region": "CONUS"},
  "Bremerton / Kitsap": {"lat": 47.5673, "lon": -122.6329, "region": "CONUS"},
  "Newport News": {"lat": 36.9788, "lon": -76.4280, "region": "CONUS"},
  "Pearl Harbor": {"lat": 21.3545, "lon": -157.9698, "region": "PACIFIC"},
  "Mayport": {"lat": 30.3918, "lon": -81.4285, "region": "CONUS"},
  "Everett": {"lat": 47.9790, "lon": -122.2021, "region": "CONUS"},
  "Pascagoula": {"lat": 30.3658, "lon": -88.5561, "region": "CONUS"},
  "Yokosuka": {"lat": 35.2831, "lon": 139.6703, "region": "WESTPAC"},
  "Sasebo": {"lat": 33.1595, "lon": 129.7235, "region": "WESTPAC"},
  "Guam": {"lat": 13.4443, "lon": 144.7937, "region": "WESTPAC"},
  "Singapore": {"lat": 1.2655, "lon": 103.8200, "region": "INDOPAC"},
  "Bahrain": {"lat": 26.2235, "lon": 50.5876, "region": "CENTCOM"},
  "Dubai": {"lat": 25.2582, "lon": 55.3047, "region": "CENTCOM"},
  "Rota": {"lat": 36.6175, "lon": -6.3497, "region": "EUCOM"},
  "South China Sea": {"lat": 12.0000, "lon": 114.0000, "region": "WESTPAC"},
  "Western Pacific (WESTPAC)": {"lat": 15.0000, "lon": 135.0000, "region": "WESTPAC"},
  "Philippine Sea": {"lat": 20.0000, "lon": 130.0000, "region": "WESTPAC"},
  "Red Sea": {"lat": 20.0000, "lon": 38.0000, "region": "CENTCOM"},
  "Persian Gulf": {"lat": 27.0000, "lon": 51.0000, "region": "CENTCOM"},
  "Gulf of Aden": {"lat": 12.5000, "lon": 47.0000, "region": "CENTCOM"},
  "Arabian Sea": {"lat": 15.0000, "lon": 65.0000, "region": "CENTCOM"},
  "Mediterranean": {"lat": 35.0000, "lon": 18.0000, "region": "EUCOM"},
  "Caribbean Sea": {"lat": 15.5000, "lon": -73.0000, "region": "SOUTHCOM"},
  "Atlantic Ocean": {"lat": 32.0000, "lon": -65.0000, "region": "ATLANTIC"},
  "Pacific Ocean": {"lat": 25.0000, "lon": -140.0000, "region": "PACIFIC"},
  "Indian Ocean": {"lat": -5.0000, "lon": 75.0000, "region": "INDOPAC"}
}
```
