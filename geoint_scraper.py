#!/usr/bin/env python3
"""
GEOINT DASHBOARD SCRAPER
Version: 1.0.0

Combined scraper for the GEOINT Dashboard that integrates:
1. Fleet Tracker data (from uscarriers.net)
2. DVIDS content with geographic coordinates
3. Breaking news categories

This scraper updates geoint.html with fresh data from all sources.

Created by @ianellisjones and IEJ Media
"""

import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from pathlib import Path
import time
import os

import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# DVIDS API Configuration
DVIDS_API_KEY = os.environ.get("DVIDS_API_KEY", "YOUR_API_KEY_HERE")
DVIDS_API_BASE = "https://api.dvidshub.net"

# Content types to fetch
CONTENT_TYPES = ["news", "image", "video"]

# Military branches to focus on
BRANCHES = ["Navy", "Marines", "Coast Guard", "Joint"]

# Maximum results per query
MAX_RESULTS_PER_QUERY = 100

# Lookback period in days
LOOKBACK_DAYS = 7

# User agent for requests
USER_AGENT = 'GEOINT-Dashboard/1.0 (Python; +https://github.com/ianellisjones/usn)'

# ==============================================================================
# LOCATION COORDINATES DATABASE
# ==============================================================================

# Geographic coordinates for mapping DVIDS content
LOCATION_COORDS = {
    # Countries
    "United States": {"lat": 39.8283, "lon": -98.5795},
    "Japan": {"lat": 36.2048, "lon": 138.2529},
    "South Korea": {"lat": 35.9078, "lon": 127.7669},
    "Germany": {"lat": 51.1657, "lon": 10.4515},
    "Italy": {"lat": 41.8719, "lon": 12.5674},
    "Spain": {"lat": 40.4637, "lon": -3.7492},
    "Bahrain": {"lat": 26.0667, "lon": 50.5577},
    "Guam": {"lat": 13.4443, "lon": 144.7937},
    "Singapore": {"lat": 1.3521, "lon": 103.8198},
    "Philippines": {"lat": 12.8797, "lon": 121.7740},
    "Australia": {"lat": -25.2744, "lon": 133.7751},
    "United Kingdom": {"lat": 55.3781, "lon": -3.4360},
    "Poland": {"lat": 51.9194, "lon": 19.1451},
    "Romania": {"lat": 45.9432, "lon": 24.9668},
    "Tunisia": {"lat": 33.8869, "lon": 9.5375},
    "Kenya": {"lat": -0.0236, "lon": 37.9062},
    "Ethiopia": {"lat": 9.1450, "lon": 40.4897},
    "Antarctica": {"lat": -82.8628, "lon": 135.0},
    "British Indian Ocean Territory": {"lat": -6.3432, "lon": 71.8765},
    "Slovakia": {"lat": 48.6690, "lon": 19.6990},
    "Cambodia": {"lat": 12.5657, "lon": 104.9910},
    "Thailand": {"lat": 15.8700, "lon": 100.9925},
    "Vietnam": {"lat": 14.0583, "lon": 108.2772},
    "Greece": {"lat": 39.0742, "lon": 21.8243},
    "Turkey": {"lat": 38.9637, "lon": 35.2433},
    "Norway": {"lat": 60.4720, "lon": 8.4689},
    "Iceland": {"lat": 64.9631, "lon": -19.0208},
    "Canada": {"lat": 56.1304, "lon": -106.3468},
    "Mexico": {"lat": 23.6345, "lon": -102.5528},
    "Kuwait": {"lat": 29.3117, "lon": 47.4818},
    "Qatar": {"lat": 25.3548, "lon": 51.1839},
    "United Arab Emirates": {"lat": 23.4241, "lon": 53.8478},
    "Oman": {"lat": 21.4735, "lon": 55.9754},
    "Saudi Arabia": {"lat": 23.8859, "lon": 45.0792},
    "Iraq": {"lat": 33.2232, "lon": 43.6793},
    "Jordan": {"lat": 30.5852, "lon": 36.2384},
    "Israel": {"lat": 31.0461, "lon": 34.8516},
    "Egypt": {"lat": 26.8206, "lon": 30.8025},
    "Djibouti": {"lat": 11.8251, "lon": 42.5903},

    # Bodies of Water
    "Pacific Ocean": {"lat": 0, "lon": -160},
    "Atlantic Ocean": {"lat": 25, "lon": -40},
    "Arabian Sea": {"lat": 15, "lon": 65},
    "South China Sea": {"lat": 12, "lon": 115},
    "Mediterranean Sea": {"lat": 35, "lon": 18},
    "Indian Ocean": {"lat": -10, "lon": 75},
    "At Sea": {"lat": 20, "lon": -60},
    "Caribbean Sea": {"lat": 15, "lon": -75},
    "Gulf of Mexico": {"lat": 25, "lon": -90},
    "Red Sea": {"lat": 20, "lon": 38},
    "Persian Gulf": {"lat": 26, "lon": 52},
    "East China Sea": {"lat": 30, "lon": 125},
    "Sea of Japan": {"lat": 40, "lon": 135},
    "Baltic Sea": {"lat": 58, "lon": 20},
    "North Sea": {"lat": 56, "lon": 3},
    "Black Sea": {"lat": 43, "lon": 34},

    # US Naval Bases / Regions
    "Norfolk": {"lat": 36.9473, "lon": -76.3134},
    "San Diego": {"lat": 32.7157, "lon": -117.1611},
    "Pearl Harbor": {"lat": 21.3069, "lon": -157.9517},
    "Yokosuka": {"lat": 35.2831, "lon": 139.6703},
    "Sasebo": {"lat": 33.1594, "lon": 129.7228},
    "Bremerton": {"lat": 47.5673, "lon": -122.6329},
    "Mayport": {"lat": 30.3930, "lon": -81.4300},
    "Pensacola": {"lat": 30.4213, "lon": -87.2169},
    "Jacksonville": {"lat": 30.3322, "lon": -81.6556},
    "Kings Bay": {"lat": 30.7991, "lon": -81.5687},
}

# Fleet ship locations (from uscarriers.net)
FLEET_LOCATIONS = {
    "Bremerton / Kitsap": {"lat": 47.5673, "lon": -122.6329, "region": "CONUS"},
    "Norfolk / Portsmouth": {"lat": 36.9473, "lon": -76.3134, "region": "CONUS"},
    "San Diego": {"lat": 32.7157, "lon": -117.1611, "region": "CONUS"},
    "Yokosuka": {"lat": 35.2831, "lon": 139.6703, "region": "WESTPAC"},
    "Sasebo": {"lat": 33.1594, "lon": 129.7228, "region": "WESTPAC"},
    "Newport News": {"lat": 36.9788, "lon": -76.428, "region": "CONUS"},
    "Pearl Harbor": {"lat": 21.3069, "lon": -157.9517, "region": "WESTPAC"},
    "Arabian Sea": {"lat": 15.0, "lon": 65.0, "region": "CENTCOM"},
    "Persian Gulf": {"lat": 26.5, "lon": 52.0, "region": "CENTCOM"},
    "Mediterranean Sea": {"lat": 35.0, "lon": 18.0, "region": "EUCOM"},
    "Caribbean Sea": {"lat": 15.5, "lon": -73.0, "region": "SOUTHCOM"},
    "Western Pacific": {"lat": 20.0, "lon": 130.0, "region": "WESTPAC"},
    "Eastern Pacific": {"lat": 10.0, "lon": -120.0, "region": "WESTPAC"},
    "Indian Ocean": {"lat": -5.0, "lon": 75.0, "region": "CENTCOM"},
    "South China Sea": {"lat": 12.0, "lon": 115.0, "region": "WESTPAC"},
    "East China Sea": {"lat": 28.0, "lon": 125.0, "region": "WESTPAC"},
    "Okinawa": {"lat": 26.3344, "lon": 127.8056, "region": "WESTPAC"},
    "Guam": {"lat": 13.4443, "lon": 144.7937, "region": "WESTPAC"},
    "Ponce": {"lat": 17.98, "lon": -66.6141, "region": "SOUTHCOM"},
    "Mayport": {"lat": 30.393, "lon": -81.43, "region": "CONUS"},
}

# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class DVIDSItem:
    """Data class representing a DVIDS content item."""
    id: str
    title: str
    description: str
    type: str
    branch: str
    unit_name: str
    date_published: str
    timestamp: str
    country: str
    state: str
    city: str
    location_display: str
    url: str
    thumbnail_url: str
    lat: float = 0.0
    lon: float = 0.0
    keywords: List[str] = field(default_factory=list)
    credit: str = ""
    duration: str = ""
    aspect_ratio: str = ""
    commands: List[str] = field(default_factory=list)
    hours_old: float = 0.0


@dataclass
class Ship:
    """Data class representing a Navy ship."""
    hull: str
    name: str
    ship_class: str
    ship_type: str
    location: str
    lat: float
    lon: float
    region: str
    date: str
    status: str
    source_url: str
    display_lat: float = 0.0
    display_lon: float = 0.0


# ==============================================================================
# DVIDS API FUNCTIONS
# ==============================================================================

def fetch_dvids_content(content_type: str, branch: str, from_date: str) -> List[dict]:
    """Fetch content from DVIDS API."""
    url = f"{DVIDS_API_BASE}/search"
    params = {
        "api_key": DVIDS_API_KEY,
        "type": content_type,
        "branch": branch,
        "from_date": from_date,
        "max_results": MAX_RESULTS_PER_QUERY,
        "sort": "date",
        "sort_order": "desc"
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 429:
            print(f"  Rate limited, waiting...")
            time.sleep(5)
            response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            print(f"  API returned status {response.status_code}")
            return []
    except Exception as e:
        print(f"  Error fetching DVIDS: {e}")
        return []


def parse_dvids_item(item: dict, content_type: str) -> Optional[DVIDSItem]:
    """Parse a DVIDS API result into a DVIDSItem."""
    try:
        # Extract basic fields
        item_id = f"{content_type}:{item.get('id', '')}"
        title = item.get("title", "").strip()
        description = item.get("short_description", item.get("description", ""))[:500]

        # Extract location
        country = item.get("country", "")
        state = item.get("state", "")
        city = item.get("city", "")

        # Build location display string
        location_parts = [p for p in [city, state, country] if p]
        location_display = ", ".join(location_parts) if location_parts else "Unknown"

        # Get coordinates
        coords = get_coordinates_for_location(country, state, city)

        # Parse date
        date_str = item.get("date", "")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            timestamp = dt.isoformat()
            date_published = dt.strftime("%b %d, %Y %H:%M UTC")
            hours_old = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
        except:
            timestamp = date_str
            date_published = date_str
            hours_old = 0

        # Extract branch
        branch = item.get("branch", "Joint")

        # Build thumbnail URL
        thumbnail_url = ""
        if content_type == "image":
            thumbnail_url = item.get("thumbnail", item.get("url", ""))
        elif content_type == "video":
            thumbnail_url = item.get("thumbnail", "")
        elif content_type == "news":
            thumbnail_url = item.get("image", {}).get("thumbnail", "") if item.get("image") else ""

        # Extract keywords
        keywords = item.get("keywords", []) if isinstance(item.get("keywords"), list) else []

        # Detect combatant commands
        commands = detect_commands(title, description, item.get("unit_name", ""))

        return DVIDSItem(
            id=item_id,
            title=title,
            description=description,
            type=content_type,
            branch=branch,
            unit_name=item.get("unit_name", ""),
            date_published=date_published,
            timestamp=timestamp,
            country=country if country else "Unknown",
            state=state,
            city=city,
            location_display=location_display,
            url=item.get("url", ""),
            thumbnail_url=thumbnail_url,
            lat=coords["lat"],
            lon=coords["lon"],
            keywords=keywords,
            credit=item.get("credit", ""),
            duration=str(item.get("duration", "")) if content_type == "video" else "",
            aspect_ratio=item.get("aspect_ratio", ""),
            commands=commands,
            hours_old=hours_old
        )
    except Exception as e:
        print(f"  Error parsing item: {e}")
        return None


def get_coordinates_for_location(country: str, state: str, city: str) -> dict:
    """Get coordinates for a location, with fallbacks."""
    # Try city-level first (future enhancement)
    # For now, use country-level coordinates

    if country in LOCATION_COORDS:
        return LOCATION_COORDS[country]

    # Try to match partial names
    country_lower = country.lower()
    for loc_name, coords in LOCATION_COORDS.items():
        if loc_name.lower() in country_lower or country_lower in loc_name.lower():
            return coords

    # Default to US center for unknown
    return {"lat": 39.8283, "lon": -98.5795}


def detect_commands(title: str, description: str, unit_name: str) -> List[str]:
    """Detect combatant commands mentioned in content."""
    commands = []
    text = f"{title} {description} {unit_name}".upper()

    command_keywords = {
        "INDOPACOM": ["INDOPACOM", "INDO-PACIFIC", "7TH FLEET", "SEVENTH FLEET", "PACIFIC FLEET"],
        "CENTCOM": ["CENTCOM", "CENTRAL COMMAND", "5TH FLEET", "FIFTH FLEET"],
        "EUCOM": ["EUCOM", "EUROPEAN COMMAND", "6TH FLEET", "SIXTH FLEET"],
        "SOUTHCOM": ["SOUTHCOM", "SOUTHERN COMMAND", "4TH FLEET", "FOURTH FLEET"],
    }

    for command, keywords in command_keywords.items():
        if any(kw in text for kw in keywords):
            commands.append(command)

    return commands


def fetch_all_dvids_content() -> List[DVIDSItem]:
    """Fetch all DVIDS content for the lookback period."""
    items = []
    seen_ids = set()

    from_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    print(f"Fetching DVIDS content from {from_date}...")

    for branch in BRANCHES:
        for content_type in CONTENT_TYPES:
            print(f"  Fetching {content_type} for {branch}...")
            results = fetch_dvids_content(content_type, branch, from_date)

            for result in results:
                item = parse_dvids_item(result, content_type)
                if item and item.id not in seen_ids:
                    items.append(item)
                    seen_ids.add(item.id)

            time.sleep(0.5)  # Rate limiting

    # Sort by timestamp (newest first)
    items.sort(key=lambda x: x.timestamp, reverse=True)

    print(f"Total DVIDS items fetched: {len(items)}")
    return items


# ==============================================================================
# FLEET SCRAPER FUNCTIONS
# ==============================================================================

def fetch_fleet_data() -> List[Ship]:
    """Fetch current fleet positions from uscarriers.net."""
    ships = []

    # Ship definitions
    carriers = [
        ("CVN68", "USS Nimitz", "Nimitz", "CVN"),
        ("CVN69", "USS Dwight D. Eisenhower", "Nimitz", "CVN"),
        ("CVN70", "USS Carl Vinson", "Nimitz", "CVN"),
        ("CVN71", "USS Theodore Roosevelt", "Nimitz", "CVN"),
        ("CVN72", "USS Abraham Lincoln", "Nimitz", "CVN"),
        ("CVN73", "USS George Washington", "Nimitz", "CVN"),
        ("CVN74", "USS John C. Stennis", "Nimitz", "CVN"),
        ("CVN75", "USS Harry S. Truman", "Nimitz", "CVN"),
        ("CVN76", "USS Ronald Reagan", "Nimitz", "CVN"),
        ("CVN77", "USS George H.W. Bush", "Nimitz", "CVN"),
        ("CVN78", "USS Gerald R. Ford", "Ford", "CVN"),
    ]

    amphibs = [
        ("LHD1", "USS Wasp", "Wasp", "LHD"),
        ("LHD2", "USS Essex", "Wasp", "LHD"),
        ("LHD3", "USS Kearsarge", "Wasp", "LHD"),
        ("LHD4", "USS Boxer", "Wasp", "LHD"),
        ("LHD5", "USS Bataan", "Wasp", "LHD"),
        ("LHD7", "USS Iwo Jima", "Wasp", "LHD"),
        ("LHD8", "USS Makin Island", "Wasp", "LHD"),
        ("LHA6", "USS America", "America", "LHA"),
        ("LHA7", "USS Tripoli", "America", "LHA"),
    ]

    all_ships = carriers + amphibs

    for hull, name, ship_class, ship_type in all_ships:
        ship_data = scrape_ship_page(hull, name, ship_class, ship_type)
        if ship_data:
            ships.append(ship_data)

    # Apply display coordinate offsets for ships at same location
    apply_display_offsets(ships)

    return ships


def scrape_ship_page(hull: str, name: str, ship_class: str, ship_type: str) -> Optional[Ship]:
    """Scrape individual ship page from uscarriers.net."""
    url = f"http://uscarriers.net/{hull.lower()}history.htm"

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"  Failed to fetch {hull}: {response.status_code}")
            return create_default_ship(hull, name, ship_class, ship_type)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the latest status (usually in first paragraph or table)
        status_text = ""
        date_text = ""
        location = "Unknown"

        # Try to find status text in various elements
        for elem in soup.find_all(['p', 'td', 'div']):
            text = elem.get_text(strip=True)
            if text and len(text) > 50 and any(word in text.lower() for word in ['moored', 'underway', 'deployed', 'anchored', 'pier']):
                status_text = text[:500]

                # Try to extract date
                date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s+\d{4})?', text)
                if date_match:
                    date_text = date_match.group(0)

                # Try to extract location
                location = extract_location(text)
                break

        # Get coordinates
        loc_data = FLEET_LOCATIONS.get(location, FLEET_LOCATIONS.get("Norfolk / Portsmouth"))
        lat = loc_data["lat"]
        lon = loc_data["lon"]
        region = loc_data.get("region", "CONUS")

        return Ship(
            hull=hull,
            name=name,
            ship_class=ship_class,
            ship_type=ship_type,
            location=location,
            lat=lat,
            lon=lon,
            region=region,
            date=date_text or "2025",
            status=status_text or f"{name} status unknown",
            source_url=url,
            display_lat=lat,
            display_lon=lon
        )

    except Exception as e:
        print(f"  Error scraping {hull}: {e}")
        return create_default_ship(hull, name, ship_class, ship_type)


def create_default_ship(hull: str, name: str, ship_class: str, ship_type: str) -> Ship:
    """Create a default ship entry when scraping fails."""
    default_loc = "Norfolk / Portsmouth" if hull.startswith("CVN") else "San Diego"
    loc_data = FLEET_LOCATIONS[default_loc]

    return Ship(
        hull=hull,
        name=name,
        ship_class=ship_class,
        ship_type=ship_type,
        location=default_loc,
        lat=loc_data["lat"],
        lon=loc_data["lon"],
        region=loc_data["region"],
        date="Unknown",
        status=f"{name} - status unavailable",
        source_url=f"http://uscarriers.net/{hull.lower()}history.htm",
        display_lat=loc_data["lat"],
        display_lon=loc_data["lon"]
    )


def extract_location(text: str) -> str:
    """Extract location from status text."""
    text_lower = text.lower()

    # Check for known locations
    location_patterns = [
        ("Arabian Sea", ["arabian sea"]),
        ("Persian Gulf", ["persian gulf"]),
        ("Mediterranean Sea", ["mediterranean"]),
        ("Caribbean Sea", ["caribbean"]),
        ("South China Sea", ["south china sea"]),
        ("Western Pacific", ["western pacific", "west pacific"]),
        ("Indian Ocean", ["indian ocean"]),
        ("Norfolk / Portsmouth", ["norfolk", "portsmouth"]),
        ("San Diego", ["san diego", "north island"]),
        ("Bremerton / Kitsap", ["bremerton", "kitsap"]),
        ("Yokosuka", ["yokosuka"]),
        ("Pearl Harbor", ["pearl harbor"]),
        ("Mayport", ["mayport"]),
        ("Okinawa", ["okinawa", "white beach"]),
        ("Guam", ["guam"]),
        ("Newport News", ["newport news"]),
        ("Ponce", ["ponce"]),
    ]

    for location, patterns in location_patterns:
        if any(p in text_lower for p in patterns):
            return location

    return "Unknown"


def apply_display_offsets(ships: List[Ship]) -> None:
    """Apply small offsets to ships at the same location for better visibility."""
    location_counts = defaultdict(int)

    for ship in ships:
        key = (ship.lat, ship.lon)
        offset = location_counts[key]

        # Apply spiral offset pattern
        angle = offset * 0.8
        radius = 3 + (offset * 0.5)

        ship.display_lat = ship.lat + (radius * 0.1 * (offset % 3 - 1))
        ship.display_lon = ship.lon + (radius * 0.15 * ((offset // 3) % 3 - 1))

        location_counts[key] += 1


# ==============================================================================
# HTML GENERATION
# ==============================================================================

def generate_geoint_html(ships: List[Ship], dvids_items: List[DVIDSItem]) -> str:
    """Generate the GEOINT Dashboard HTML with updated data."""

    # Read the template
    template_path = Path(__file__).parent / "geoint.html"

    if not template_path.exists():
        print("Error: geoint.html template not found")
        return ""

    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Convert ships to JSON
    ships_json = json.dumps([asdict(s) for s in ships], indent=None)

    # Find and replace the shipsData
    ships_pattern = r'const shipsData = \[.*?\];'
    ships_replacement = f'const shipsData = {ships_json};'
    html = re.sub(ships_pattern, ships_replacement, html, flags=re.DOTALL)

    # Update timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = re.sub(
        r"Last Update: <span id=\"lastUpdate\">.*?</span>",
        f'Last Update: <span id="lastUpdate">{timestamp}</span>',
        html
    )

    return html


def save_dvids_data(items: List[DVIDSItem]) -> None:
    """Save DVIDS data to JSON file."""
    # Calculate statistics
    by_country = defaultdict(int)
    by_type = defaultdict(int)
    by_branch = defaultdict(int)
    by_command = defaultdict(int)

    for item in items:
        by_country[item.country] += 1
        by_type[item.type] += 1
        by_branch[item.branch] += 1
        for cmd in item.commands:
            by_command[cmd] += 1

    data = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "timestamp": datetime.utcnow().isoformat(),
        "total_count": len(items),
        "by_country": dict(by_country),
        "by_type": dict(by_type),
        "by_branch": dict(by_branch),
        "by_command": dict(by_command),
        "items": [asdict(item) for item in items]
    }

    output_path = Path(__file__).parent / "dvids_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Saved DVIDS data to {output_path}")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point for the GEOINT scraper."""
    print("=" * 60)
    print("GEOINT DASHBOARD SCRAPER")
    print("=" * 60)
    print()

    # Fetch fleet data
    print("Fetching fleet data...")
    ships = fetch_fleet_data()
    print(f"  Found {len(ships)} ships")
    print()

    # Fetch DVIDS data
    print("Fetching DVIDS content...")
    dvids_items = fetch_all_dvids_content()
    print()

    # Save DVIDS data
    save_dvids_data(dvids_items)
    print()

    # Generate HTML
    print("Generating GEOINT Dashboard...")
    html = generate_geoint_html(ships, dvids_items)

    if html:
        output_path = Path(__file__).parent / "geoint.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Saved to {output_path}")

    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
