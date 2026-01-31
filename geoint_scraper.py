#!/usr/bin/env python3
"""
GEOINT DASHBOARD SCRAPER
Version: 1.1.0

Combined scraper for the GEOINT Dashboard that integrates:
1. Fleet Tracker data (static data - updated manually)
2. DVIDS content with geographic coordinates
3. Breaking news categories

This scraper updates geoint.html with fresh DVIDS data while preserving
static fleet data.

Created by @ianellisjones and IEJ Media
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from pathlib import Path
import time
import os

import requests

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
USER_AGENT = 'GEOINT-Dashboard/1.1 (Python; +https://github.com/ianellisjones/usn)'

# GitHub Pages URL for fetching existing data
GITHUB_PAGES_BASE = "https://ianellisjones.github.io/usn"

# ==============================================================================
# STATIC FLEET DATA
# ==============================================================================

# Current fleet positions (manually updated)
# Last updated: 2026-01-30
STATIC_SHIPS_DATA = [
    {"hull": "CVN68", "name": "USS Nimitz", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Bremerton / Kitsap", "lat": 47.5673, "lon": -122.6329, "region": "CONUS", "date": "2025", "status": "USS Nimitz moored at Delta Pier on Naval Base Kitsap-Bremerton following an extended nine-month deployment in the U.S. 5th and 7th Fleet AoR.", "source_url": "", "display_lat": 47.5673, "display_lon": -119.6329},
    {"hull": "CVN69", "name": "USS Dwight D. Eisenhower", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "Jan. 8", "status": "September 26, USS Dwight D. Eisenhower moored at Pier 12N on Naval Station Norfolk after a six-day underway for TRACOM-CQ, in the Jacksonville Op. Area; Moved \"dead-stick\" to Super Pier 5N in Norfolk Naval Shipyard, for a Planned Incremental Availability (PIA), on Jan. 8.", "source_url": "", "display_lat": 36.9473, "display_lon": -71.3134},
    {"hull": "CVN70", "name": "USS Carl Vinson", "ship_class": "Nimitz", "ship_type": "CVN", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "September 16", "status": "September 16, The Carl Vinson moored at Juliet Pier on Naval Air Station North Island after a three-day underway for ammo offload.", "source_url": "", "display_lat": 32.7157, "display_lon": -112.1611},
    {"hull": "CVN71", "name": "USS Theodore Roosevelt", "ship_class": "Nimitz", "ship_type": "CVN", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "Jan. 21", "status": "January 15, 2026 USS Theodore Roosevelt moored at Berth Lima on Naval Air Station North Island after a one-day underway in the SOCAL Op. Area; Underway for FRS-CQ from Jan. 21-28.", "source_url": "", "display_lat": 37.69534607176052, "display_lon": -114.2861},
    {"hull": "CVN72", "name": "USS Abraham Lincoln", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Arabian Sea", "lat": 15.0, "lon": 65.0, "region": "CENTCOM", "date": "January 26", "status": "January 26, USS Abraham Lincoln CSG recently arrived on station in the North Arabian Sea, off the east coast of Oman.", "source_url": "", "display_lat": 15.0, "display_lon": 65.0},
    {"hull": "CVN73", "name": "USS George Washington", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Yokosuka", "lat": 35.2831, "lon": 139.6703, "region": "WESTPAC", "date": "2025", "status": "USS George Washington moored at Berth 12 on Fleet Activities Yokosuka following a two-month patrol.", "source_url": "", "display_lat": 35.2831, "display_lon": 139.6703},
    {"hull": "CVN74", "name": "USS John C. Stennis", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Newport News", "lat": 36.9788, "lon": -76.428, "region": "CONUS", "date": "April 8", "status": "April 8, 2024 USS John C. Stennis undocked and moored at Outfitting Berth #1 on Newport News Shipyard.", "source_url": "", "display_lat": 36.9788, "display_lon": -76.428},
    {"hull": "CVN75", "name": "USS Harry S. Truman", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "Jan. 21", "status": "September 26, The Harry S. Truman moored at Pier 14S on Naval Station Norfolk; Moved to Pier 14N on Sept. 28; Brief underway on Oct. 8; Moved to Pier 12N on Jan. 21, 2026.", "source_url": "", "display_lat": 41.92694607176052, "display_lon": -73.4384},
    {"hull": "CVN76", "name": "USS Ronald Reagan", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Bremerton / Kitsap", "lat": 47.5673, "lon": -122.6329, "region": "CONUS", "date": "Dec. 2", "status": "November 12, USS Ronald Reagan moored at Bravo Pier on Naval Base Kitsap-Bremerton; Underway for FRS-CQ, in the SOCAL Op. Area, from Dec. 2-13.", "source_url": "", "display_lat": 47.5673, "display_lon": -126.08290000000001},
    {"hull": "CVN77", "name": "USS George H.W. Bush", "ship_class": "Nimitz", "ship_type": "CVN", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "January 27", "status": "January 27, 2026 USS George H.W. Bush moored at Pier 14S on Naval Station Norfolk after a two-week underway for FRS-CQ, in the Virginia Capes and Key West Op. Areas.", "source_url": "", "display_lat": 41.27742701892219, "display_lon": -78.8134},
    {"hull": "CVN78", "name": "USS Gerald R. Ford", "ship_class": "Ford", "ship_type": "CVN", "location": "Caribbean Sea", "lat": 15.5, "lon": -73.0, "region": "SOUTHCOM", "date": "Jan. 27", "status": "January 21, USS Gerald R. Ford anchored approx. 1 n.m. off the coast of Charlotte Amalie West, St. Thomas Island, U.S. Virgin Islands, for a five-day liberty port visit; Conducted operations southwest of Puerto Rico from Jan. 27-29.", "source_url": "", "display_lat": 15.5, "display_lon": -73.0},
    {"hull": "LHD1", "name": "USS Wasp", "ship_class": "Wasp", "ship_type": "LHD", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "May 19", "status": "April 14, USS Wasp moored at Berth 6, Pier 11 on Naval Station Norfolk after a 10-day underway for deck landing qualifications, in the Virginia Capes Op. Area; Underway again on April 28; Moored at Berth 6, Pier 6 on May 9; Moved \"dead-stick\" to Pier 1 in BAE Systems shipyard on May 19.", "source_url": "", "display_lat": 36.9473, "display_lon": -82.0634},
    {"hull": "LHD2", "name": "USS Essex", "ship_class": "Wasp", "ship_type": "LHD", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "January 24", "status": "January 24, 2026 USS Essex moored at Berth 5, Pier 2 on Naval Base San Diego after a two-day underway in the SOCAL Op. Area.", "source_url": "", "display_lat": 37.04582701892219, "display_lon": -119.6611},
    {"hull": "LHD3", "name": "USS Kearsarge", "ship_class": "Wasp", "ship_type": "LHD", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "December 12", "status": "December 12, The Kearsarge moored at Berth 1, Pier 10 on Naval Station Norfolk.", "source_url": "", "display_lat": 32.61717298107781, "display_lon": -78.8134},
    {"hull": "LHD4", "name": "USS Boxer", "ship_class": "Wasp", "ship_type": "LHD", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "Jan. 21", "status": "November 4, USS Boxer moored at Berth 6, Pier 13 on Naval Base San Diego for a brief stop; Returned home on Nov. 12; Underway for Amphibious Squadron (PHIBRON) 1/Marine Expeditionary Unit Integration Training (PMINT), with the 11th MEU, from Dec. 2-15; Underway for ARG/MEUEX on Jan. 21.", "source_url": "", "display_lat": 32.7157, "display_lon": -122.9111},
    {"hull": "LHD5", "name": "USS Bataan", "ship_class": "Wasp", "ship_type": "LHD", "location": "Norfolk / Portsmouth", "lat": 36.9473, "lon": -76.3134, "region": "CONUS", "date": "2025", "status": "July 2025 USS Bataan undocked and moored at Berth 2E on NASSCO shipyard.", "source_url": "", "display_lat": 31.96765392823948, "display_lon": -73.4384},
    {"hull": "LHD7", "name": "USS Iwo Jima", "ship_class": "Wasp", "ship_type": "LHD", "location": "Ponce", "lat": 17.98, "lon": -66.6141, "region": "SOUTHCOM", "date": "Jan. 15", "status": "January 2, 2026 The Iwo Jima ARG recently arrived northeast of Orchila Island, Venezuela, in support of Operation Absolute Resolve; Moored at Wharf C2 on Naval Station Mayport from Jan. 7-11; Moored at Berth 4/5 in Port of Ponce from Jan. 15-20.", "source_url": "", "display_lat": 17.98, "display_lon": -66.6141},
    {"hull": "LHD8", "name": "USS Makin Island", "ship_class": "Wasp", "ship_type": "LHD", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "Jan. 23", "status": "January 21, USS Makin Island departed Naval Base San Diego for a Quarterly Underway Amphibious Readiness Training 26.2; Anchored off Camp Pendleton from Jan. 23-24.", "source_url": "", "display_lat": 28.385572981077807, "display_lon": -119.6611},
    {"hull": "LHA6", "name": "USS America", "ship_class": "America", "ship_type": "LHA", "location": "San Diego", "lat": 32.7157, "lon": -117.1611, "region": "CONUS", "date": "2027", "status": "USS America moored at Berth 5, Pier 13 in its new homeport of Naval Base San Diego after forward-deployed to Japan for nearly six years.", "source_url": "", "display_lat": 27.73605392823948, "display_lon": -114.2861},
    {"hull": "LHA7", "name": "USS Tripoli", "ship_class": "America", "ship_type": "LHA", "location": "Okinawa", "lat": 26.3344, "lon": 127.8056, "region": "WESTPAC", "date": "2026", "status": "The Tripoli recently moored at Navy Pier East on White Beach Naval Facility.", "source_url": "", "display_lat": 26.3344, "display_lon": 127.8056}
]

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
# FLEET DATA FUNCTIONS
# ==============================================================================

def get_fleet_data() -> List[dict]:
    """
    Get fleet data from static source.

    Note: Previously fetched from uscarriers.net which is currently offline.
    Using static data that can be manually updated when new information is available.
    """
    print("Using static fleet data (last updated: 2026-01-30)")
    return STATIC_SHIPS_DATA.copy()


def try_fetch_fleet_from_github() -> Optional[List[dict]]:
    """
    Try to fetch latest fleet data from GitHub Pages as fallback.
    Returns None if fetch fails.
    """
    try:
        print("Attempting to fetch latest fleet data from GitHub Pages...")
        url = f"{GITHUB_PAGES_BASE}/index.html"
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            # Extract shipsData from the HTML
            match = re.search(r'const shipsData = (\[.*?\]);', response.text, re.DOTALL)
            if match:
                ships_json = match.group(1)
                ships = json.loads(ships_json)
                print(f"  Successfully fetched {len(ships)} ships from GitHub Pages")
                return ships
    except Exception as e:
        print(f"  Could not fetch from GitHub Pages: {e}")

    return None


# ==============================================================================
# HTML GENERATION
# ==============================================================================

def generate_geoint_html(ships: List[dict], dvids_items: List[DVIDSItem]) -> str:
    """Generate the GEOINT Dashboard HTML with updated data."""

    # Read the template
    template_path = Path(__file__).parent / "geoint.html"

    if not template_path.exists():
        print("Error: geoint.html template not found")
        return ""

    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Convert ships to JSON
    ships_json = json.dumps(ships, indent=None)

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
    print("GEOINT DASHBOARD SCRAPER v1.1")
    print("=" * 60)
    print()

    # Get fleet data (try GitHub first, fall back to static)
    print("Getting fleet data...")
    ships = try_fetch_fleet_from_github()
    if ships is None:
        ships = get_fleet_data()
    print(f"  Using {len(ships)} ships")
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
