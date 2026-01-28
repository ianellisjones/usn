#!/usr/bin/env python3
"""
US NAVY BIG DECK FLEET TRACKER - Automated Scraper
Version: 5.1.0

Standalone script for GitHub Actions automation.
Scrapes fleet data and generates a self-contained HTML file.

Data Source: USCarriers.net (with permission)
"""

import re
import json
import math
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIGURATION
# ==============================================================================

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Ship Database with hull numbers and names
SHIP_DATABASE = {
    # Aircraft Carriers (CVN)
    "CVN68": {"name": "USS Nimitz", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn68history.htm"},
    "CVN69": {"name": "USS Dwight D. Eisenhower", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn69history.htm"},
    "CVN70": {"name": "USS Carl Vinson", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn70history.htm"},
    "CVN71": {"name": "USS Theodore Roosevelt", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn71history.htm"},
    "CVN72": {"name": "USS Abraham Lincoln", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn72history.htm"},
    "CVN73": {"name": "USS George Washington", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn73history.htm"},
    "CVN74": {"name": "USS John C. Stennis", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn74history.htm"},
    "CVN75": {"name": "USS Harry S. Truman", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn75history.htm"},
    "CVN76": {"name": "USS Ronald Reagan", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn76history.htm"},
    "CVN77": {"name": "USS George H.W. Bush", "class": "Nimitz", "type": "CVN", "url": "http://uscarriers.net/cvn77history.htm"},
    "CVN78": {"name": "USS Gerald R. Ford", "class": "Ford", "type": "CVN", "url": "http://uscarriers.net/cvn78history.htm"},
    # Amphibious Assault Ships (LHA/LHD)
    "LHD1": {"name": "USS Wasp", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd1history.htm"},
    "LHD2": {"name": "USS Essex", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd2history.htm"},
    "LHD3": {"name": "USS Kearsarge", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd3history.htm"},
    "LHD4": {"name": "USS Boxer", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd4history.htm"},
    "LHD5": {"name": "USS Bataan", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd5history.htm"},
    "LHD7": {"name": "USS Iwo Jima", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd7history.htm"},
    "LHD8": {"name": "USS Makin Island", "class": "Wasp", "type": "LHD", "url": "http://uscarriers.net/lhd8history.htm"},
    "LHA6": {"name": "USS America", "class": "America", "type": "LHA", "url": "http://uscarriers.net/lha6history.htm"},
    "LHA7": {"name": "USS Tripoli", "class": "America", "type": "LHA", "url": "http://uscarriers.net/lha7history.htm"},
}

# Comprehensive coordinate database
LOCATION_COORDS = {
    # US PORTS / SHIPYARDS
    "Norfolk / Portsmouth": {"lat": 36.9473, "lon": -76.3134, "region": "CONUS"},
    "San Diego": {"lat": 32.7157, "lon": -117.1611, "region": "CONUS"},
    "Bremerton / Kitsap": {"lat": 47.5673, "lon": -122.6329, "region": "CONUS"},
    "Newport News": {"lat": 36.9788, "lon": -76.4280, "region": "CONUS"},
    "Pearl Harbor": {"lat": 21.3545, "lon": -157.9698, "region": "PACIFIC"},
    "Mayport": {"lat": 30.3918, "lon": -81.4285, "region": "CONUS"},
    "Everett": {"lat": 47.9790, "lon": -122.2021, "region": "CONUS"},
    "Pascagoula": {"lat": 30.3658, "lon": -88.5561, "region": "CONUS"},

    # FORWARD DEPLOYED / FOREIGN PORTS
    "Yokosuka": {"lat": 35.2831, "lon": 139.6703, "region": "WESTPAC"},
    "Sasebo": {"lat": 33.1595, "lon": 129.7235, "region": "WESTPAC"},
    "Guam": {"lat": 13.4443, "lon": 144.7937, "region": "WESTPAC"},
    "Singapore": {"lat": 1.2655, "lon": 103.8200, "region": "INDOPAC"},
    "Bahrain": {"lat": 26.2235, "lon": 50.5876, "region": "CENTCOM"},
    "Dubai": {"lat": 25.2582, "lon": 55.3047, "region": "CENTCOM"},
    "Busan": {"lat": 35.1028, "lon": 129.0403, "region": "WESTPAC"},
    "Philippines": {"lat": 14.5995, "lon": 120.9842, "region": "WESTPAC"},
    "Malaysia": {"lat": 3.1390, "lon": 101.6869, "region": "INDOPAC"},
    "Okinawa": {"lat": 26.3344, "lon": 127.8056, "region": "WESTPAC"},

    # STRATEGIC REGIONS / SEAS
    "South China Sea": {"lat": 12.0000, "lon": 114.0000, "region": "WESTPAC"},
    "Western Pacific (WESTPAC)": {"lat": 15.0000, "lon": 135.0000, "region": "WESTPAC"},
    "Philippine Sea": {"lat": 20.0000, "lon": 130.0000, "region": "WESTPAC"},
    "Red Sea": {"lat": 20.0000, "lon": 38.0000, "region": "CENTCOM"},
    "Persian Gulf": {"lat": 27.0000, "lon": 51.0000, "region": "CENTCOM"},
    "Gulf of Oman": {"lat": 24.5000, "lon": 58.5000, "region": "CENTCOM"},
    "Gulf of Aden": {"lat": 12.5000, "lon": 47.0000, "region": "CENTCOM"},
    "Arabian Sea": {"lat": 15.0000, "lon": 65.0000, "region": "CENTCOM"},
    "Mediterranean": {"lat": 35.0000, "lon": 18.0000, "region": "EUCOM"},
    "Caribbean Sea": {"lat": 15.5000, "lon": -73.0000, "region": "SOUTHCOM"},
    "North Sea": {"lat": 56.0000, "lon": 3.0000, "region": "EUCOM"},
    "Norwegian Sea": {"lat": 68.0000, "lon": 5.0000, "region": "EUCOM"},
    "Strait of Gibraltar": {"lat": 35.9500, "lon": -5.6000, "region": "EUCOM"},
    "Suez Canal": {"lat": 30.6000, "lon": 32.3300, "region": "CENTCOM"},
    "Bab el-Mandeb": {"lat": 12.5833, "lon": 43.3333, "region": "CENTCOM"},
    "Sea of Japan": {"lat": 40.0000, "lon": 135.0000, "region": "WESTPAC"},

    # OCEANS
    "Atlantic Ocean": {"lat": 30.0000, "lon": -45.0000, "region": "ATLANTIC"},
    "Pacific Ocean": {"lat": 20.0000, "lon": -150.0000, "region": "PACIFIC"},
    "Indian Ocean": {"lat": -5.0000, "lon": 75.0000, "region": "INDOPAC"},

    # FALLBACK
    "Underway / Unknown": {"lat": 0.0000, "lon": 0.0000, "region": "UNKNOWN"},
}


@dataclass
class ShipStatus:
    """Data class representing a ship's current status."""
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
# SCRAPER ENGINE
# ==============================================================================

def fetch_history_text(url: str, char_limit: int = 50000) -> str:
    """Fetches raw HTML content, strips tags, returns the tail of the text."""
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        full_text = soup.get_text(separator='\n')
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        return clean_text[-char_limit:] if len(clean_text) > char_limit else clean_text
    except requests.RequestException as e:
        return f"ERROR: {str(e)}"


def parse_status_entry(text_block: str) -> Tuple[str, str]:
    """Parses text block to find the most recent status entry."""
    lines = text_block.split('\n')

    current_year = "Unknown"
    years_found = re.findall(r'(202[3-7])', text_block)
    if years_found:
        priority_years = [y for y in years_found if y in ['2024', '2025', '2026']]
        current_year = priority_years[-1] if priority_years else years_found[-1]

    processed_lines = []
    running_year = current_year

    for line in lines:
        year_match = re.search(r'^202[3-7]', line)
        if year_match:
            running_year = year_match.group(0)
        processed_lines.append({'text': line, 'year': running_year})

    keywords = [
        "moored", "anchored", "underway", "arrived", "departed",
        "transited", "operations", "returned", "participated", "conducted",
        "moved to", "visited", "pulled into", "sea trials", "flight deck",
        "undocked", "homeport"
    ]
    allowed_years = ["2024", "2025", "2026", "2027"]

    for entry in reversed(processed_lines):
        text_lower = entry['text'].lower()
        year = entry['year']
        if year in allowed_years and any(k in text_lower for k in keywords):
            if text_lower.strip().startswith("from ") and " - " in text_lower:
                continue
            return year, entry['text']

    return current_year, "No recent status found."


def categorize_location(text: str) -> str:
    """Maps keywords in status text to location tags."""
    text_lower = text.lower()

    departure_overrides = {
        "departed san diego": "Pacific Ocean",
        "departed norfolk": "Atlantic Ocean",
        "departed pearl harbor": "Pacific Ocean",
        "departed mayport": "Atlantic Ocean",
        "departed bremerton": "Pacific Ocean",
        "departed yokosuka": "Western Pacific (WESTPAC)",
        "departed sasebo": "Western Pacific (WESTPAC)",
    }

    for phrase, location in departure_overrides.items():
        if phrase in text_lower:
            return location

    location_map = {
        "South China Sea": ["south china sea", "spratly islands", "spratly", "luzon"],
        "Western Pacific (WESTPAC)": ["san bernardino strait", "western pacific", "westpac"],
        "Philippine Sea": ["philippine sea"],
        "Red Sea": ["red sea"],
        "Persian Gulf": ["persian gulf", "arabian gulf"],
        "Gulf of Oman": ["gulf of oman"],
        "Gulf of Aden": ["gulf of aden"],
        "Arabian Sea": ["arabian sea"],
        "Mediterranean": ["mediterranean", "med sea"],
        "Caribbean Sea": ["caribbean", "st. croix", "trinidad", "tobago", "puerto rico", "virgin islands"],
        "North Sea": ["north sea"],
        "Norwegian Sea": ["norwegian sea"],
        "Strait of Gibraltar": ["gibraltar"],
        "Suez Canal": ["suez"],
        "Bab el-Mandeb": ["bab el-mandeb"],
        "Sea of Japan": ["sea of japan"],
        "Norfolk / Portsmouth": ["norfolk", "portsmouth", "virginia beach", "naval station norfolk", "pier 1", "pier 11", "pier 12", "pier 14"],
        "San Diego": ["san diego", "north island", "camp pendleton", "nassco san diego"],
        "Bremerton / Kitsap": ["bremerton", "kitsap", "psns"],
        "Newport News": ["newport news", "huntington ingalls", "outfitting berth"],
        "Yokosuka": ["yokosuka"],
        "Pearl Harbor": ["pearl harbor"],
        "Mayport": ["mayport"],
        "Everett": ["everett"],
        "Singapore": ["singapore", "changi"],
        "Bahrain": ["bahrain", "manama"],
        "Dubai": ["dubai", "jebel ali"],
        "Busan": ["busan"],
        "Guam": ["guam", "apra"],
        "Sasebo": ["sasebo", "juliet basin"],
        "Malaysia": ["malaysia", "klang"],
        "Philippines": ["philippines", "manila", "subic"],
        "Pascagoula": ["pascagoula", "ingalls"],
        "Okinawa": ["okinawa", "white beach"],
        "Atlantic Ocean": ["atlantic"],
        "Pacific Ocean": ["pacific"],
        "Indian Ocean": ["indian ocean"],
    }

    for label, keywords in location_map.items():
        if any(k in text_lower for k in keywords):
            return label

    return "Underway / Unknown"


def extract_date(text: str) -> str:
    """Extracts the last specific date mentioned in the text."""
    pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[-1] if matches else "Date Unspecified"


def apply_location_offsets(ships: List[ShipStatus]) -> List[ShipStatus]:
    """Applies coordinate offsets to ships at the same location."""
    location_groups = defaultdict(list)
    for ship in ships:
        location_groups[ship.location].append(ship)

    for location, group in location_groups.items():
        count = len(group)
        if count == 1:
            group[0].display_lat = group[0].lat
            group[0].display_lon = group[0].lon
        else:
            offset_distance = 2.0 if count <= 4 else 2.5 if count <= 8 else 3.0
            for i, ship in enumerate(group):
                angle = (2 * math.pi * i) / count
                ship.display_lat = ship.lat + offset_distance * math.sin(angle)
                ship.display_lon = ship.lon + offset_distance * math.cos(angle)

    return ships


def scrape_fleet() -> List[ShipStatus]:
    """Scrapes all ships and returns list of ShipStatus objects."""
    results = []
    total = len(SHIP_DATABASE)

    print("\n" + "="*70)
    print("  US NAVY BIG DECK FLEET TRACKER - SCANNING")
    print("="*70 + "\n")

    for i, (hull, ship_info) in enumerate(SHIP_DATABASE.items(), 1):
        print(f"  [{i:2}/{total}] Scanning {hull} - {ship_info['name']}...", end=" ")

        raw_text = fetch_history_text(ship_info['url'])

        if "ERROR" in raw_text:
            print("FAILED")
            continue

        year, status = parse_status_entry(raw_text)
        location = categorize_location(status)
        date_str = extract_date(status)

        if date_str == "Date Unspecified":
            date_str = year

        coords = LOCATION_COORDS.get(location, LOCATION_COORDS["Underway / Unknown"])

        ship_status = ShipStatus(
            hull=hull,
            name=ship_info['name'],
            ship_class=ship_info['class'],
            ship_type=ship_info['type'],
            location=location,
            lat=coords['lat'],
            lon=coords['lon'],
            region=coords['region'],
            date=date_str,
            status=status,
            source_url=ship_info['url'],
            display_lat=coords['lat'],
            display_lon=coords['lon']
        )
        results.append(ship_status)
        print(f"OK - {location}")

    results = apply_location_offsets(results)

    print("\n" + "="*70)
    print(f"  SCAN COMPLETE: {len(results)} ships tracked")
    print("="*70 + "\n")

    return results


# ==============================================================================
# HTML GENERATOR
# ==============================================================================

def generate_globe_html(ships: List[ShipStatus]) -> str:
    """Generates complete HTML page with interactive 3D globe."""

    ships_data = [asdict(s) for s in ships]
    ships_json = json.dumps(ships_data)

    cvn_count = len([s for s in ships if s.ship_type == "CVN"])
    lha_lhd_count = len([s for s in ships if s.ship_type in ["LHA", "LHD"]])

    location_counts = defaultdict(list)
    for s in ships:
        location_counts[s.location].append(s.hull)
    location_summary = json.dumps({loc: hulls for loc, hulls in location_counts.items()})

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US NAVY BIG DECK FLEET TRACKER</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0f; color: #e0e0e0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; overflow: hidden; height: 100vh; }}
        .container {{ display: grid; grid-template-columns: 1fr 360px; grid-template-rows: auto 1fr; height: 100vh; gap: 0; }}
        .header {{ grid-column: 1 / -1; background: linear-gradient(180deg, #111118 0%, #0a0a0f 100%); border-bottom: 1px solid #1e1e2e; padding: 14px 28px; display: flex; justify-content: space-between; align-items: center; }}
        .header-left {{ display: flex; align-items: center; gap: 20px; }}
        .logo {{ font-size: 20px; font-weight: 700; color: #00ff88; letter-spacing: 1px; }}
        .logo-sub {{ font-size: 11px; font-weight: 500; color: #666; letter-spacing: 2px; margin-top: 2px; text-transform: uppercase; }}
        .status-bar {{ display: flex; gap: 40px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: 700; color: #00ffff; }}
        .stat-value.cvn {{ color: #ff6b6b; }}
        .stat-value.amphib {{ color: #4ecdc4; }}
        .stat-label {{ font-size: 10px; font-weight: 600; color: #555; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }}
        .timestamp {{ font-size: 11px; color: #444; font-weight: 500; }}
        .timestamp span {{ color: #00ff88; }}
        .globe-container {{ background: #0a0a0f; position: relative; }}
        #globe {{ width: 100%; height: 100%; }}
        .side-panel {{ background: #0d0d14; border-left: 1px solid #1e1e2e; display: flex; flex-direction: column; overflow: hidden; }}
        .panel-header {{ padding: 16px 20px; border-bottom: 1px solid #1e1e2e; }}
        .panel-title {{ font-size: 12px; font-weight: 600; color: #00ff88; letter-spacing: 2px; text-transform: uppercase; }}
        .ship-list {{ flex: 1; overflow-y: auto; padding: 12px; }}
        .ship-list::-webkit-scrollbar {{ width: 5px; }}
        .ship-list::-webkit-scrollbar-track {{ background: #0a0a0f; }}
        .ship-list::-webkit-scrollbar-thumb {{ background: #333; border-radius: 3px; }}
        .ship-list::-webkit-scrollbar-thumb:hover {{ background: #00ff88; }}
        .location-group {{ margin-bottom: 16px; }}
        .location-header {{ display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(0, 255, 136, 0.05); border-radius: 6px; margin-bottom: 8px; cursor: pointer; transition: background 0.2s; }}
        .location-header:hover {{ background: rgba(0, 255, 136, 0.1); }}
        .location-name {{ flex: 1; font-size: 12px; font-weight: 600; color: #00ff88; }}
        .location-count {{ font-size: 11px; font-weight: 600; color: #888; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; }}
        .ship-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid #1e1e2e; border-radius: 8px; margin-bottom: 6px; margin-left: 12px; padding: 12px 14px; cursor: pointer; transition: all 0.15s ease; }}
        .ship-card:hover {{ border-color: #333; background: rgba(255, 255, 255, 0.04); }}
        .ship-card.active {{ border-color: #00ffff; background: rgba(0, 255, 255, 0.08); }}
        .ship-card.cvn {{ border-left: 3px solid #ff6b6b; }}
        .ship-card.amphib {{ border-left: 3px solid #4ecdc4; }}
        .ship-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .ship-hull {{ font-size: 14px; font-weight: 700; color: #fff; }}
        .ship-hull.cvn {{ color: #ff6b6b; }}
        .ship-hull.amphib {{ color: #4ecdc4; }}
        .ship-type {{ font-size: 9px; font-weight: 600; padding: 3px 8px; border-radius: 4px; background: rgba(255, 255, 255, 0.06); color: #888; letter-spacing: 0.5px; }}
        .ship-name {{ font-size: 12px; color: #777; font-weight: 500; }}
        .ship-date {{ font-size: 10px; color: #444; margin-top: 4px; font-weight: 500; }}
        .detail-panel {{ background: #111118; border-top: 1px solid #1e1e2e; padding: 16px; max-height: 280px; overflow-y: auto; }}
        .detail-panel.hidden {{ display: none; }}
        .detail-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
        .detail-title {{ font-size: 15px; font-weight: 700; color: #00ffff; }}
        .detail-close {{ cursor: pointer; color: #555; font-size: 18px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 4px; transition: all 0.15s; }}
        .detail-close:hover {{ color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }}
        .detail-row {{ display: flex; margin-bottom: 8px; }}
        .detail-label {{ width: 70px; font-size: 10px; font-weight: 600; color: #444; text-transform: uppercase; letter-spacing: 0.5px; }}
        .detail-value {{ flex: 1; font-size: 13px; color: #aaa; font-weight: 500; }}
        .detail-status {{ font-size: 12px; color: #00ff88; line-height: 1.6; padding: 12px; background: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-top: 12px; font-weight: 500; }}
        .filter-bar {{ padding: 12px 16px; border-bottom: 1px solid #1e1e2e; display: flex; gap: 8px; }}
        .filter-btn {{ font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; padding: 6px 14px; background: transparent; border: 1px solid #2a2a3a; color: #666; cursor: pointer; border-radius: 6px; transition: all 0.15s; }}
        .filter-btn:hover {{ border-color: #444; color: #999; }}
        .filter-btn.active {{ background: rgba(0, 255, 136, 0.1); border-color: #00ff88; color: #00ff88; }}
        .attribution {{ padding: 10px 16px; border-top: 1px solid #1e1e2e; font-size: 10px; color: #333; text-align: center; font-weight: 500; }}
        .attribution a {{ color: #444; text-decoration: none; }}
        .attribution a:hover {{ color: #00ff88; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <div>
                    <div class="logo">FLEET TRACKER</div>
                    <div class="logo-sub">US Navy Big Deck Operations</div>
                </div>
            </div>
            <div class="status-bar">
                <div class="stat">
                    <div class="stat-value">{len(ships)}</div>
                    <div class="stat-label">Total Ships</div>
                </div>
                <div class="stat">
                    <div class="stat-value cvn">{cvn_count}</div>
                    <div class="stat-label">Carriers</div>
                </div>
                <div class="stat">
                    <div class="stat-value amphib">{lha_lhd_count}</div>
                    <div class="stat-label">Amphibs</div>
                </div>
            </div>
            <div class="timestamp">
                Last Update: <span>{timestamp}</span>
            </div>
        </header>
        <div class="globe-container">
            <div id="globe"></div>
        </div>
        <div class="side-panel">
            <div class="panel-header">
                <div class="panel-title">Fleet Status</div>
            </div>
            <div class="filter-bar">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="CVN">CVN</button>
                <button class="filter-btn" data-filter="LHA">LHA</button>
                <button class="filter-btn" data-filter="LHD">LHD</button>
            </div>
            <div class="ship-list" id="shipList"></div>
            <div class="detail-panel hidden" id="detailPanel">
                <div class="detail-header">
                    <div class="detail-title" id="detailTitle">-</div>
                    <span class="detail-close" onclick="closeDetail()">&#x2715;</span>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Class</div>
                    <div class="detail-value" id="detailClass">-</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Location</div>
                    <div class="detail-value" id="detailLocation">-</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Region</div>
                    <div class="detail-value" id="detailRegion">-</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">As Of</div>
                    <div class="detail-value" id="detailDate">-</div>
                </div>
                <div class="detail-status" id="detailStatus">-</div>
            </div>
            <div class="attribution">
                Data: <a href="http://uscarriers.net" target="_blank">USCarriers.net</a>
            </div>
        </div>
    </div>
    <script>
        const shipsData = {ships_json};
        const locationSummary = {location_summary};
        let activeFilter = 'all';
        let selectedShip = null;

        function initGlobe() {{
            const cvnShips = shipsData.filter(s => s.ship_type === 'CVN');
            const amphibShips = shipsData.filter(s => s.ship_type !== 'CVN');

            const cvnTrace = {{
                type: 'scattergeo', mode: 'markers+text',
                lat: cvnShips.map(s => s.display_lat), lon: cvnShips.map(s => s.display_lon),
                text: cvnShips.map(s => s.hull), textposition: 'top center',
                textfont: {{ family: 'Inter, sans-serif', size: 10, color: '#ff6b6b', weight: 600 }},
                hoverinfo: 'text', hovertext: cvnShips.map(s => `<b>${{s.hull}}</b><br>${{s.name}}<br>${{s.location}}`),
                marker: {{ size: 12, color: '#ff6b6b', symbol: 'diamond', line: {{ width: 2, color: '#cc4444' }} }},
                name: 'Carriers (CVN)', customdata: cvnShips
            }};

            const amphibTrace = {{
                type: 'scattergeo', mode: 'markers+text',
                lat: amphibShips.map(s => s.display_lat), lon: amphibShips.map(s => s.display_lon),
                text: amphibShips.map(s => s.hull), textposition: 'top center',
                textfont: {{ family: 'Inter, sans-serif', size: 9, color: '#4ecdc4', weight: 600 }},
                hoverinfo: 'text', hovertext: amphibShips.map(s => `<b>${{s.hull}}</b><br>${{s.name}}<br>${{s.location}}`),
                marker: {{ size: 10, color: '#4ecdc4', symbol: 'circle', line: {{ width: 2, color: '#2a9d8f' }} }},
                name: 'Amphibs (LHA/LHD)', customdata: amphibShips
            }};

            const layout = {{
                geo: {{
                    projection: {{ type: 'orthographic', rotation: {{ lon: -100, lat: 25 }} }},
                    showland: true, landcolor: '#1a1a2e', showocean: true, oceancolor: '#0a0a0f',
                    showlakes: false, showrivers: false, showcountries: true, countrycolor: '#2a2a4e', countrywidth: 0.5,
                    showcoastlines: true, coastlinecolor: '#00ff88', coastlinewidth: 0.8, showframe: false, bgcolor: 'rgba(0,0,0,0)',
                    lonaxis: {{ showgrid: true, gridcolor: 'rgba(0, 255, 136, 0.08)', gridwidth: 0.5 }},
                    lataxis: {{ showgrid: true, gridcolor: 'rgba(0, 255, 136, 0.08)', gridwidth: 0.5 }}
                }},
                paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: {{ t: 0, b: 0, l: 0, r: 0 }},
                showlegend: true, legend: {{ x: 0.02, y: 0.98, bgcolor: 'rgba(10, 10, 15, 0.9)', bordercolor: '#1e1e2e', borderwidth: 1, font: {{ family: 'Inter, sans-serif', size: 11, color: '#888' }} }},
                dragmode: 'pan'
            }};

            const config = {{ responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'], displaylogo: false, scrollZoom: true }};
            Plotly.newPlot('globe', [cvnTrace, amphibTrace], layout, config);
            document.getElementById('globe').on('plotly_click', function(data) {{
                if (data.points && data.points.length > 0) {{
                    const ship = data.points[0].customdata;
                    if (ship) {{ showDetail(ship); highlightShipCard(ship.hull); }}
                }}
            }});
        }}

        function renderShipList() {{
            const container = document.getElementById('shipList');
            const filtered = activeFilter === 'all' ? shipsData : shipsData.filter(s => s.ship_type === activeFilter);
            const grouped = {{}};
            filtered.forEach(ship => {{ if (!grouped[ship.location]) grouped[ship.location] = []; grouped[ship.location].push(ship); }});
            const sortedLocations = Object.keys(grouped).sort((a, b) => grouped[b].length - grouped[a].length);
            let html = '';
            sortedLocations.forEach(location => {{
                const ships = grouped[location];
                const count = ships.length;
                html += `<div class="location-group"><div class="location-header" onclick="rotateToLocation('${{location}}')"><span class="location-name">${{location}}</span><span class="location-count">${{count}} ship${{count > 1 ? 's' : ''}}</span></div>`;
                ships.forEach(ship => {{
                    const typeClass = ship.ship_type === 'CVN' ? 'cvn' : 'amphib';
                    html += `<div class="ship-card ${{typeClass}}" data-hull="${{ship.hull}}" onclick="selectShip('${{ship.hull}}')"><div class="ship-header"><span class="ship-hull ${{typeClass}}">${{ship.hull}}</span><span class="ship-type">${{ship.ship_type}}</span></div><div class="ship-name">${{ship.name}}</div><div class="ship-date">As of ${{ship.date}}</div></div>`;
                }});
                html += '</div>';
            }});
            container.innerHTML = html;
        }}

        function rotateToLocation(location) {{ const ship = shipsData.find(s => s.location === location); if (ship) Plotly.relayout('globe', {{ 'geo.projection.rotation.lon': ship.lon, 'geo.projection.rotation.lat': Math.max(-60, Math.min(60, ship.lat)) }}); }}
        function selectShip(hull) {{ const ship = shipsData.find(s => s.hull === hull); if (ship) {{ showDetail(ship); highlightShipCard(hull); Plotly.relayout('globe', {{ 'geo.projection.rotation.lon': ship.lon, 'geo.projection.rotation.lat': Math.max(-60, Math.min(60, ship.lat)) }}); }} }}
        function highlightShipCard(hull) {{ document.querySelectorAll('.ship-card').forEach(card => card.classList.remove('active')); const card = document.querySelector(`.ship-card[data-hull="${{hull}}"]`); if (card) {{ card.classList.add('active'); card.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }} }}
        function showDetail(ship) {{ selectedShip = ship; document.getElementById('detailPanel').classList.remove('hidden'); document.getElementById('detailTitle').textContent = `${{ship.hull}} - ${{ship.name}}`; document.getElementById('detailClass').textContent = `${{ship.ship_class}}-class ${{ship.ship_type}}`; document.getElementById('detailLocation').textContent = ship.location; document.getElementById('detailRegion').textContent = ship.region; document.getElementById('detailDate').textContent = ship.date; document.getElementById('detailStatus').textContent = ship.status; }}
        function closeDetail() {{ document.getElementById('detailPanel').classList.add('hidden'); document.querySelectorAll('.ship-card').forEach(card => card.classList.remove('active')); selectedShip = null; }}
        document.querySelectorAll('.filter-btn').forEach(btn => {{ btn.addEventListener('click', function() {{ document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active')); this.classList.add('active'); activeFilter = this.dataset.filter; renderShipList(); }}); }});
        initGlobe(); renderShipList();
    </script>
</body>
</html>'''

    return html


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point for the scraper."""
    print("Starting Fleet Tracker Scraper...")

    # Scrape fleet data
    fleet_data = scrape_fleet()

    if not fleet_data:
        print("ERROR: No fleet data scraped!")
        return 1

    # Generate HTML
    html_content = generate_globe_html(fleet_data)

    # Save to index.html for GitHub Pages
    output_file = Path("index.html")
    output_file.write_text(html_content, encoding='utf-8')

    print(f"\n>>> HTML file saved: {output_file}")
    print(f"    Ships tracked: {len(fleet_data)}")
    print(f"    Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    return 0


if __name__ == "__main__":
    exit(main())
