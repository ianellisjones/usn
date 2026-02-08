#!/usr/bin/env python3
"""
U.S. NAVY DESTROYER TRACKER - Automated Scraper
Version: 1.0.0

Standalone script for GitHub Actions automation.
Scrapes destroyer data and generates a self-contained HTML file.

Created by @ianellisjones and IEJ Media
"""

import re
import json
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIGURATION
# ==============================================================================

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Destroyer Database - Arleigh Burke class (Flight I, II, IIA, III) and Zumwalt class
SHIP_DATABASE = {
    # Flight I
    "DDG51": {"name": "USS Arleigh Burke", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg51history.htm"},
    "DDG52": {"name": "USS Barry", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg52history.htm"},
    "DDG53": {"name": "USS John Paul Jones", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg53history.htm"},
    "DDG54": {"name": "USS Curtis Wilbur", "class": "Arleigh Burke", "flight": "I", "homeport": "WESTPAC", "url": "http://uscarriers.net/ddg54history.htm"},
    "DDG55": {"name": "USS Stout", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg55history.htm"},
    "DDG56": {"name": "USS John S. McCain", "class": "Arleigh Burke", "flight": "I", "homeport": "WESTPAC", "url": "http://uscarriers.net/ddg56history.htm"},
    "DDG57": {"name": "USS Mitscher", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg57history.htm"},
    "DDG58": {"name": "USS Laboon", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg58history.htm"},
    "DDG59": {"name": "USS Russell", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg59history.htm"},
    "DDG60": {"name": "USS Paul Hamilton", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg60history.htm"},
    "DDG61": {"name": "USS Ramage", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg61history.htm"},
    "DDG62": {"name": "USS Fitzgerald", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg62history.htm"},
    "DDG63": {"name": "USS Stethem", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg63history.htm"},
    "DDG64": {"name": "USS Carney", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg64history.htm"},
    "DDG65": {"name": "USS Benfold", "class": "Arleigh Burke", "flight": "I", "homeport": "WESTPAC", "url": "http://uscarriers.net/ddg65history.htm"},
    "DDG66": {"name": "USS Gonzalez", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg66history.htm"},
    "DDG67": {"name": "USS Cole", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg67history.htm"},
    "DDG68": {"name": "USS The Sullivans", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg68history.htm"},
    "DDG69": {"name": "USS Milius", "class": "Arleigh Burke", "flight": "I", "homeport": "WESTPAC", "url": "http://uscarriers.net/ddg69history.htm"},
    "DDG70": {"name": "USS Hopper", "class": "Arleigh Burke", "flight": "I", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg70history.htm"},
    "DDG71": {"name": "USS Ross", "class": "Arleigh Burke", "flight": "I", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg71history.htm"},
    # Flight II
    "DDG72": {"name": "USS Mahan", "class": "Arleigh Burke", "flight": "II", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg72history.htm"},
    "DDG73": {"name": "USS Decatur", "class": "Arleigh Burke", "flight": "II", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg73history.htm"},
    "DDG74": {"name": "USS McFaul", "class": "Arleigh Burke", "flight": "II", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg74history.htm"},
    "DDG75": {"name": "USS Donald Cook", "class": "Arleigh Burke", "flight": "II", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg75history.htm"},
    "DDG76": {"name": "USS Higgins", "class": "Arleigh Burke", "flight": "II", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg76history.htm"},
    "DDG77": {"name": "USS O'Kane", "class": "Arleigh Burke", "flight": "II", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg77history.htm"},
    "DDG78": {"name": "USS Porter", "class": "Arleigh Burke", "flight": "II", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg78history.htm"},
    # Flight IIA
    "DDG79": {"name": "USS Oscar Austin", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg79history.htm"},
    "DDG80": {"name": "USS Roosevelt", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg80history.htm"},
    "DDG81": {"name": "USS Winston S. Churchill", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg81history.htm"},
    "DDG82": {"name": "USS Lassen", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg82history.htm"},
    "DDG83": {"name": "USS Howard", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg83history.htm"},
    "DDG84": {"name": "USS Bulkeley", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg84history.htm"},
    "DDG85": {"name": "USS McCampbell", "class": "Arleigh Burke", "flight": "IIA", "homeport": "WESTPAC", "url": "http://uscarriers.net/ddg85history.htm"},
    "DDG86": {"name": "USS Shoup", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg86history.htm"},
    "DDG87": {"name": "USS Mason", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg87history.htm"},
    "DDG88": {"name": "USS Preble", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg88history.htm"},
    "DDG89": {"name": "USS Mustin", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg89history.htm"},
    "DDG90": {"name": "USS Chafee", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg90history.htm"},
    "DDG91": {"name": "USS Pinckney", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg91history.htm"},
    "DDG92": {"name": "USS Momsen", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg92history.htm"},
    "DDG93": {"name": "USS Chung-Hoon", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg93history.htm"},
    "DDG94": {"name": "USS Nitze", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg94history.htm"},
    "DDG95": {"name": "USS James E. Williams", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg95history.htm"},
    "DDG96": {"name": "USS Bainbridge", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg96history.htm"},
    "DDG97": {"name": "USS Halsey", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg97history.htm"},
    "DDG98": {"name": "USS Forrest Sherman", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg98history.htm"},
    "DDG99": {"name": "USS Farragut", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg99history.htm"},
    "DDG100": {"name": "USS Kidd", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg100history.htm"},
    "DDG101": {"name": "USS Gridley", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg101history.htm"},
    "DDG102": {"name": "USS Sampson", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg102history.htm"},
    "DDG103": {"name": "USS Truxtun", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg103history.htm"},
    "DDG104": {"name": "USS Sterett", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg104history.htm"},
    "DDG105": {"name": "USS Dewey", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg105history.htm"},
    "DDG106": {"name": "USS Stockdale", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg106history.htm"},
    "DDG107": {"name": "USS Gravely", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg107history.htm"},
    "DDG108": {"name": "USS Wayne E. Meyer", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg108history.htm"},
    "DDG109": {"name": "USS Jason Dunham", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg109history.htm"},
    "DDG110": {"name": "USS William P. Lawrence", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg110history.htm"},
    "DDG111": {"name": "USS Spruance", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg111history.htm"},
    "DDG112": {"name": "USS Michael Murphy", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg112history.htm"},
    "DDG113": {"name": "USS John Finn", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg113history.htm"},
    "DDG114": {"name": "USS Ralph Johnson", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg114history.htm"},
    "DDG115": {"name": "USS Rafael Peralta", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg115history.htm"},
    "DDG116": {"name": "USS Thomas Hudner", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg116history.htm"},
    "DDG117": {"name": "USS Paul Ignatius", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg117history.htm"},
    "DDG118": {"name": "USS Daniel Inouye", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg118history.htm"},
    "DDG119": {"name": "USS Delbert D. Black", "class": "Arleigh Burke", "flight": "IIA", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg119history.htm"},
    "DDG120": {"name": "USS Carl M. Levin", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg120history.htm"},
    "DDG121": {"name": "USS Frank E. Petersen Jr.", "class": "Arleigh Burke", "flight": "IIA", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg121history.htm"},
    # Flight III
    "DDG122": {"name": "USS John Basilone", "class": "Arleigh Burke", "flight": "III", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg122history.htm"},
    "DDG123": {"name": "USS Lenah Sutcliffe Higbee", "class": "Arleigh Burke", "flight": "III", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg123history.htm"},
    "DDG125": {"name": "USS Jack H. Lucas", "class": "Arleigh Burke", "flight": "III", "homeport": "ATLANTIC", "url": "http://uscarriers.net/ddg125history.htm"},
    # Zumwalt class
    "DDG1000": {"name": "USS Zumwalt", "class": "Zumwalt", "flight": "N/A", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg1000history.htm"},
    "DDG1001": {"name": "USS Michael Monsoor", "class": "Zumwalt", "flight": "N/A", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg1001history.htm"},
    "DDG1002": {"name": "USS Lyndon B. Johnson", "class": "Zumwalt", "flight": "N/A", "homeport": "PACIFIC", "url": "http://uscarriers.net/ddg1002history.htm"},
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
    "Bath": {"lat": 43.9106, "lon": -69.8206, "region": "CONUS"},
    "Rota": {"lat": 36.6175, "lon": -6.3497, "region": "EUCOM"},

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
    "East China Sea": {"lat": 28.0000, "lon": 125.0000, "region": "WESTPAC"},
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
    "Baltic Sea": {"lat": 55.0000, "lon": 15.0000, "region": "EUCOM"},
    "Black Sea": {"lat": 43.0000, "lon": 35.0000, "region": "EUCOM"},

    # OCEANS - Default positions based on homeport
    "Atlantic Ocean": {"lat": 32.0000, "lon": -65.0000, "region": "ATLANTIC"},
    "Pacific Ocean": {"lat": 25.0000, "lon": -140.0000, "region": "PACIFIC"},
    "Indian Ocean": {"lat": -5.0000, "lon": 75.0000, "region": "INDOPAC"},
}

# Location keywords - ordered list for finding LAST match
LOCATION_KEYWORDS = [
    # Most specific locations first (ports, bases)
    ("Rota", ["rota", "naval station rota"]),
    ("Bath", ["bath iron works", "bath maine", "biw"]),
    ("Okinawa", ["okinawa", "white beach"]),
    ("Sasebo", ["sasebo", "juliet basin"]),
    ("Yokosuka", ["yokosuka"]),
    ("Norfolk / Portsmouth", ["norfolk", "portsmouth", "virginia beach", "naval station norfolk", "pier 11", "pier 12", "pier 14", "bae systems shipyard", "nassco"]),
    ("San Diego", ["san diego", "north island", "naval base san diego"]),
    ("Bremerton / Kitsap", ["bremerton", "kitsap", "psns", "puget sound"]),
    ("Newport News", ["newport news", "huntington ingalls"]),
    ("Pearl Harbor", ["pearl harbor"]),
    ("Mayport", ["mayport", "naval station mayport"]),
    ("Everett", ["everett"]),
    ("Pascagoula", ["pascagoula", "ingalls"]),
    ("Guam", ["guam", "apra"]),
    ("Singapore", ["singapore", "changi"]),
    ("Bahrain", ["bahrain", "manama"]),
    ("Dubai", ["dubai", "jebel ali"]),
    ("Busan", ["busan"]),
    ("Philippines", ["philippines", "manila", "subic"]),
    ("Malaysia", ["malaysia", "klang"]),

    # Regions / Seas
    ("Caribbean Sea", ["caribbean", "venezuela", "st. croix", "puerto rico", "virgin islands"]),
    ("South China Sea", ["south china sea", "spratly islands"]),
    ("Western Pacific (WESTPAC)", ["western pacific", "westpac"]),
    ("Philippine Sea", ["philippine sea"]),
    ("East China Sea", ["east china sea"]),
    ("Red Sea", ["red sea"]),
    ("Persian Gulf", ["persian gulf", "arabian gulf"]),
    ("Gulf of Oman", ["gulf of oman"]),
    ("Gulf of Aden", ["gulf of aden"]),
    ("Arabian Sea", ["arabian sea"]),
    ("Mediterranean", ["mediterranean", "med sea"]),
    ("North Sea", ["north sea"]),
    ("Norwegian Sea", ["norwegian sea"]),
    ("Baltic Sea", ["baltic"]),
    ("Black Sea", ["black sea"]),
    ("Strait of Gibraltar", ["gibraltar"]),
    ("Suez Canal", ["suez"]),
    ("Bab el-Mandeb", ["bab el-mandeb"]),
    ("Sea of Japan", ["sea of japan"]),

    # Broad oceans (lowest priority)
    ("Atlantic Ocean", ["atlantic"]),
    ("Pacific Ocean", ["pacific"]),
    ("Indian Ocean", ["indian ocean"]),
]


@dataclass
class ShipStatus:
    """Data class representing a ship's current status."""
    hull: str
    name: str
    ship_class: str
    flight: str
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
        priority_years = [y for y in years_found if y in ['2025', '2026', '2027']]
        if not priority_years:
            priority_years = [y for y in years_found if y in ['2024']]
        current_year = priority_years[-1] if priority_years else years_found[-1]

    processed_lines = []
    running_year = current_year

    for line in lines:
        year_match = re.search(r'^(202[3-7])', line)
        if year_match:
            running_year = year_match.group(0)
        processed_lines.append({'text': line, 'year': running_year})

    keywords = [
        "moored", "anchored", "underway", "arrived", "departed",
        "transited", "operations", "returned", "participated", "conducted",
        "moved to", "visited", "pulled into", "sea trials", "flight deck",
        "undocked", "homeport", "recently", "deployed"
    ]
    allowed_years = ["2025", "2026", "2027"]

    # First try to find 2025/2026/2027 entries
    for entry in reversed(processed_lines):
        text_lower = entry['text'].lower()
        year = entry['year']
        if year in allowed_years and any(k in text_lower for k in keywords):
            if text_lower.strip().startswith("from ") and " - " in text_lower:
                continue
            return year, entry['text']

    # Fallback to 2024 if no recent entries
    for entry in reversed(processed_lines):
        text_lower = entry['text'].lower()
        year = entry['year']
        if year == "2024" and any(k in text_lower for k in keywords):
            if text_lower.strip().startswith("from ") and " - " in text_lower:
                continue
            return year, entry['text']

    return current_year, "No recent status found."


def categorize_location(text: str, homeport: str = "ATLANTIC") -> str:
    """Maps keywords in status text to location tags."""
    text_lower = text.lower()

    # Check for departure phrases
    departure_patterns = [
        ("departed san diego", "Pacific Ocean"),
        ("departed norfolk", "Atlantic Ocean"),
        ("departed pearl harbor", "Pacific Ocean"),
        ("departed mayport", "Atlantic Ocean"),
        ("departed everett", "Pacific Ocean"),
        ("departed yokosuka", "Western Pacific (WESTPAC)"),
        ("departed sasebo", "Western Pacific (WESTPAC)"),
        ("departed rota", "Mediterranean"),
    ]

    for phrase, loc in departure_patterns:
        if phrase in text_lower:
            dep_idx = text_lower.rfind(phrase)
            remaining_text = text_lower[dep_idx + len(phrase):]
            has_subsequent = False
            for loc_name, keywords in LOCATION_KEYWORDS:
                for kw in keywords:
                    if kw in remaining_text:
                        has_subsequent = True
                        break
                if has_subsequent:
                    break
            if not has_subsequent:
                return loc

    # Find the LAST (rightmost) location mentioned in the text
    last_match = None
    last_position = -1

    for location_name, keywords in LOCATION_KEYWORDS:
        for keyword in keywords:
            idx = text_lower.rfind(keyword)
            if idx > last_position:
                last_position = idx
                last_match = location_name

    if last_match:
        return last_match

    # No location found - return default based on homeport
    if homeport == "PACIFIC":
        return "Pacific Ocean"
    elif homeport == "WESTPAC":
        return "Western Pacific (WESTPAC)"
    else:
        return "Atlantic Ocean"


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
            # Use larger offsets for very crowded ports
            if count <= 3:
                offset_distance = 2.0
            elif count <= 6:
                offset_distance = 2.5
            elif count <= 10:
                offset_distance = 3.0
            elif count <= 15:
                offset_distance = 3.5
            else:
                offset_distance = 4.0

            for i, ship in enumerate(group):
                angle = (2 * math.pi * i) / count
                radius = offset_distance * (1.0 + 0.1 * (i % 3))
                ship.display_lat = ship.lat + radius * math.sin(angle)
                ship.display_lon = ship.lon + radius * math.cos(angle)

    return ships


def scrape_fleet() -> List[ShipStatus]:
    """Scrapes all destroyers and returns list of ShipStatus objects."""
    results = []
    total = len(SHIP_DATABASE)

    print("\n" + "="*70)
    print("  U.S. NAVY DESTROYER TRACKER - SCANNING")
    print("="*70 + "\n")

    for i, (hull, ship_info) in enumerate(SHIP_DATABASE.items(), 1):
        print(f"  [{i:2}/{total}] Scanning {hull} - {ship_info['name']}...", end=" ")

        raw_text = fetch_history_text(ship_info['url'])

        if "ERROR" in raw_text:
            print("FAILED")
            continue

        year, status = parse_status_entry(raw_text)
        location = categorize_location(status, ship_info.get('homeport', 'ATLANTIC'))
        date_str = extract_date(status)

        if date_str == "Date Unspecified":
            date_str = year

        coords = LOCATION_COORDS.get(location)
        if not coords:
            homeport = ship_info.get('homeport', 'ATLANTIC')
            if homeport == "PACIFIC":
                coords = LOCATION_COORDS["Pacific Ocean"]
            elif homeport == "WESTPAC":
                coords = LOCATION_COORDS["Western Pacific (WESTPAC)"]
            else:
                coords = LOCATION_COORDS["Atlantic Ocean"]

        ship_status = ShipStatus(
            hull=hull,
            name=ship_info['name'],
            ship_class=ship_info['class'],
            flight=ship_info['flight'],
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
    print(f"  SCAN COMPLETE: {len(results)} destroyers tracked")
    print("="*70 + "\n")

    return results


# ==============================================================================
# HTML GENERATOR
# ==============================================================================

def generate_globe_html(ships: List[ShipStatus]) -> str:
    """Generates complete HTML page with interactive 3D globe."""

    ships_data = [asdict(s) for s in ships]
    ships_json = json.dumps(ships_data)

    burke_count = len([s for s in ships if s.ship_class == "Arleigh Burke"])
    zumwalt_count = len([s for s in ships if s.ship_class == "Zumwalt"])

    location_groups = defaultdict(list)
    for s in ships:
        location_groups[s.location].append(asdict(s))
    location_groups_json = json.dumps(dict(location_groups))

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>U.S. NAVY DESTROYER TRACKER</title>
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
        .stat-value.burke {{ color: #ffa726; }}
        .stat-value.zumwalt {{ color: #ab47bc; }}
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
        .location-group {{ margin-bottom: 16px; }}
        .location-header {{ display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(0, 255, 136, 0.05); border-radius: 6px; margin-bottom: 8px; cursor: pointer; transition: background 0.2s; }}
        .location-header:hover {{ background: rgba(0, 255, 136, 0.1); }}
        .location-name {{ flex: 1; font-size: 12px; font-weight: 600; color: #00ff88; }}
        .location-count {{ font-size: 11px; font-weight: 600; color: #888; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; }}
        .ship-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid #1e1e2e; border-radius: 8px; margin-bottom: 6px; margin-left: 12px; padding: 12px 14px; cursor: pointer; transition: all 0.15s ease; }}
        .ship-card:hover {{ border-color: #333; background: rgba(255, 255, 255, 0.04); }}
        .ship-card.active {{ border-color: #00ffff; background: rgba(0, 255, 255, 0.08); }}
        .ship-card.burke {{ border-left: 3px solid #ffa726; }}
        .ship-card.zumwalt {{ border-left: 3px solid #ab47bc; }}
        .ship-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .ship-hull {{ font-size: 14px; font-weight: 700; color: #fff; }}
        .ship-hull.burke {{ color: #ffa726; }}
        .ship-hull.zumwalt {{ color: #ab47bc; }}
        .ship-type {{ font-size: 9px; font-weight: 600; padding: 3px 8px; border-radius: 4px; background: rgba(255, 255, 255, 0.06); color: #888; }}
        .ship-name {{ font-size: 12px; color: #777; font-weight: 500; }}
        .ship-date {{ font-size: 10px; color: #444; margin-top: 4px; font-weight: 500; }}
        .detail-panel {{ background: #111118; border-top: 1px solid #1e1e2e; padding: 16px; max-height: 280px; overflow-y: auto; }}
        .detail-panel.hidden {{ display: none; }}
        .detail-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
        .detail-title {{ font-size: 15px; font-weight: 700; color: #00ffff; }}
        .detail-close {{ cursor: pointer; color: #555; font-size: 18px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 4px; }}
        .detail-close:hover {{ color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }}
        .detail-row {{ display: flex; margin-bottom: 8px; }}
        .detail-label {{ width: 70px; font-size: 10px; font-weight: 600; color: #444; text-transform: uppercase; }}
        .detail-value {{ flex: 1; font-size: 13px; color: #aaa; font-weight: 500; }}
        .detail-status {{ font-size: 12px; color: #00ff88; line-height: 1.6; padding: 12px; background: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-top: 12px; }}
        .filter-bar {{ padding: 12px 16px; border-bottom: 1px solid #1e1e2e; display: flex; gap: 8px; flex-wrap: wrap; }}
        .filter-btn {{ font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; padding: 6px 14px; background: transparent; border: 1px solid #2a2a3a; color: #666; cursor: pointer; border-radius: 6px; transition: all 0.15s; }}
        .filter-btn:hover {{ border-color: #444; color: #999; }}
        .filter-btn.active {{ background: rgba(0, 255, 136, 0.1); border-color: #00ff88; color: #00ff88; }}
        .attribution {{ padding: 10px 16px; border-top: 1px solid #1e1e2e; font-size: 10px; color: #444; text-align: center; }}
        .btn-group {{ display: flex; gap: 12px; align-items: center; }}
        .ddg-btn {{ font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; padding: 10px 20px; background: linear-gradient(135deg, #ffa726 0%, #e65100 100%); border: none; color: #fff; cursor: pointer; border-radius: 8px; transition: all 0.2s; box-shadow: 0 2px 8px rgba(255, 167, 38, 0.3); }}
        .ddg-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(255, 167, 38, 0.4); }}
        .cocom-dropdown {{ position: relative; }}
        .cocom-btn {{ font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; padding: 10px 20px; background: linear-gradient(135deg, #4ecdc4 0%, #2a9d8f 100%); border: none; color: #fff; cursor: pointer; border-radius: 8px; transition: all 0.2s; box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3); display: flex; align-items: center; gap: 8px; }}
        .cocom-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(78, 205, 196, 0.4); }}
        .cocom-btn::after {{ content: '▼'; font-size: 8px; }}
        .cocom-menu {{ position: absolute; top: 100%; left: 0; margin-top: 8px; background: #111118; border: 1px solid #2a2a3a; border-radius: 10px; min-width: 180px; overflow: hidden; opacity: 0; visibility: hidden; transform: translateY(-10px); transition: all 0.2s; z-index: 100; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
        .cocom-dropdown.open .cocom-menu {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        .cocom-item {{ padding: 12px 16px; cursor: pointer; font-size: 12px; font-weight: 500; color: #888; transition: all 0.15s; border-bottom: 1px solid #1e1e2e; }}
        .cocom-item:last-child {{ border-bottom: none; }}
        .cocom-item:hover {{ background: rgba(78, 205, 196, 0.1); color: #4ecdc4; }}
        .cocom-panel {{ position: absolute; bottom: 20px; left: 20px; background: rgba(17, 17, 24, 0.95); border: 1px solid #2a2a3a; border-radius: 12px; width: 320px; max-height: 350px; overflow: hidden; opacity: 0; visibility: hidden; transform: translateY(20px); transition: all 0.3s; z-index: 50; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
        .cocom-panel.visible {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        .cocom-panel-header {{ padding: 14px 16px; border-bottom: 1px solid #1e1e2e; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(180deg, rgba(78, 205, 196, 0.1) 0%, transparent 100%); }}
        .cocom-panel-title {{ font-size: 13px; font-weight: 700; color: #4ecdc4; }}
        .cocom-panel-close {{ cursor: pointer; color: #555; font-size: 18px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 4px; }}
        .cocom-panel-close:hover {{ color: #ff6b6b; background: rgba(255,107,107,0.1); }}
        .cocom-panel-body {{ padding: 12px; max-height: 280px; overflow-y: auto; }}
        .cocom-ship {{ display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }}
        .cocom-ship:hover {{ background: rgba(255,255,255,0.05); }}
        .cocom-ship-icon {{ width: 8px; height: 8px; border-radius: 2px; }}
        .cocom-ship-icon.burke {{ background: #ffa726; }}
        .cocom-ship-icon.zumwalt {{ background: #ab47bc; }}
        .cocom-ship-hull {{ font-size: 12px; font-weight: 600; color: #fff; width: 60px; }}
        .cocom-ship-name {{ font-size: 11px; color: #666; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .cocom-ship-loc {{ font-size: 10px; color: #4ecdc4; }}
        .location-callout {{ position: absolute; background: rgba(17, 17, 24, 0.95); border: 1px solid #2a2a3a; border-radius: 10px; padding: 12px; min-width: 220px; max-width: 300px; z-index: 60; box-shadow: 0 8px 32px rgba(0,0,0,0.4); pointer-events: auto; max-height: 400px; overflow-y: auto; }}
        .location-callout-header {{ font-size: 11px; font-weight: 600; color: #00ff88; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #1e1e2e; position: sticky; top: 0; background: rgba(17, 17, 24, 0.95); }}
        .location-callout-ship {{ display: flex; align-items: center; gap: 8px; padding: 5px 0; cursor: pointer; }}
        .location-callout-ship:hover {{ background: rgba(255,255,255,0.03); margin: 0 -8px; padding: 5px 8px; border-radius: 4px; }}
        .location-callout-icon {{ width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }}
        .location-callout-icon.burke {{ background: #ffa726; }}
        .location-callout-icon.zumwalt {{ background: #ab47bc; }}
        .location-callout-hull {{ font-size: 11px; font-weight: 600; color: #fff; }}
        .location-callout-hull.burke {{ color: #ffa726; }}
        .location-callout-hull.zumwalt {{ color: #ab47bc; }}
        .location-callout-name {{ font-size: 10px; color: #666; margin-left: auto; }}
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.85); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; visibility: hidden; transition: all 0.3s ease; }}
        .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
        .modal {{ background: #111118; border: 1px solid #2a2a3a; border-radius: 16px; width: 90%; max-width: 900px; max-height: 85vh; overflow: hidden; transform: scale(0.9); transition: transform 0.3s ease; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); }}
        .modal-overlay.visible .modal {{ transform: scale(1); }}
        .modal-header {{ padding: 20px 24px; border-bottom: 1px solid #1e1e2e; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(180deg, #1a1a22 0%, #111118 100%); }}
        .modal-title {{ font-size: 18px; font-weight: 700; color: #ffa726; }}
        .modal-subtitle {{ font-size: 11px; color: #666; margin-top: 4px; }}
        .modal-close {{ cursor: pointer; color: #555; font-size: 24px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 8px; }}
        .modal-close:hover {{ color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }}
        .modal-body {{ padding: 16px 24px 24px; overflow-y: auto; max-height: calc(85vh - 100px); }}
        .ddg-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }}
        .ddg-item {{ background: rgba(255, 167, 38, 0.05); border: 1px solid rgba(255, 167, 38, 0.2); border-radius: 10px; padding: 12px 14px; cursor: pointer; transition: all 0.15s; }}
        .ddg-item:hover {{ background: rgba(255, 167, 38, 0.1); border-color: rgba(255, 167, 38, 0.4); transform: translateY(-2px); }}
        .ddg-item.zumwalt {{ background: rgba(171, 71, 188, 0.05); border-color: rgba(171, 71, 188, 0.2); }}
        .ddg-item.zumwalt:hover {{ background: rgba(171, 71, 188, 0.1); border-color: rgba(171, 71, 188, 0.4); }}
        .ddg-hull {{ font-size: 14px; font-weight: 700; color: #ffa726; margin-bottom: 2px; }}
        .ddg-item.zumwalt .ddg-hull {{ color: #ab47bc; }}
        .ddg-name {{ font-size: 11px; color: #888; font-weight: 500; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .ddg-location {{ font-size: 10px; color: #00ff88; font-weight: 600; padding: 3px 8px; background: rgba(0, 255, 136, 0.1); border-radius: 4px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <div>
                    <div class="logo">U.S. NAVY DESTROYER TRACKER</div>
                    <div class="logo-sub">Guided Missile Destroyer Squadron</div>
                </div>
            </div>
            <div class="status-bar">
                <div class="stat">
                    <div class="stat-value">{len(ships)}</div>
                    <div class="stat-label">Total DDGs</div>
                </div>
                <div class="stat">
                    <div class="stat-value burke">{burke_count}</div>
                    <div class="stat-label">Arleigh Burke</div>
                </div>
                <div class="stat">
                    <div class="stat-value zumwalt">{zumwalt_count}</div>
                    <div class="stat-label">Zumwalt</div>
                </div>
            </div>
            <div class="btn-group">
                <button class="ddg-btn" onclick="showDDGModal()">Where are the destroyers?</button>
                <div class="cocom-dropdown" id="cocomDropdown">
                    <button class="cocom-btn" onclick="toggleCocomMenu()">By Theater</button>
                    <div class="cocom-menu">
                        <div class="cocom-item" onclick="selectCocom('INDOPACOM')">INDOPACOM</div>
                        <div class="cocom-item" onclick="selectCocom('CENTCOM')">CENTCOM</div>
                        <div class="cocom-item" onclick="selectCocom('EUCOM')">EUCOM</div>
                        <div class="cocom-item" onclick="selectCocom('SOUTHCOM')">SOUTHCOM</div>
                        <div class="cocom-item" onclick="selectCocom('CONUS')">CONUS</div>
                    </div>
                </div>
            </div>
        </header>
        <div class="globe-container">
            <div id="globe"></div>
            <div class="cocom-panel" id="cocomPanel">
                <div class="cocom-panel-header">
                    <div class="cocom-panel-title" id="cocomPanelTitle">INDOPACOM</div>
                    <span class="cocom-panel-close" onclick="closeCocomPanel()">&#x2715;</span>
                </div>
                <div class="cocom-panel-body" id="cocomPanelBody"></div>
            </div>
            <div id="locationCallouts"></div>
        </div>
        <div class="side-panel">
            <div class="panel-header">
                <div class="panel-title">Destroyer Fleet Status</div>
            </div>
            <div class="filter-bar">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="I">Flight I</button>
                <button class="filter-btn" data-filter="II">Flight II</button>
                <button class="filter-btn" data-filter="IIA">Flight IIA</button>
                <button class="filter-btn" data-filter="III">Flight III</button>
                <button class="filter-btn" data-filter="Zumwalt">Zumwalt</button>
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
                    <div class="detail-label">Flight</div>
                    <div class="detail-value" id="detailFlight">-</div>
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
                Created by @ianellisjones and IEJ Media
                <div class="timestamp" style="margin-top: 6px;">
                    Last Update: <span>{timestamp}</span>
                </div>
            </div>
        </div>
    </div>
    <div class="modal-overlay" id="ddgModal" onclick="closeDDGModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <div class="modal-title">WHERE ARE THE DESTROYERS?</div>
                    <div class="modal-subtitle">Current positions of all U.S. Navy guided missile destroyers</div>
                </div>
                <span class="modal-close" onclick="closeDDGModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="ddg-grid" id="ddgGrid"></div>
            </div>
        </div>
    </div>
    <script>
        const shipsData = {ships_json};
        const locationGroups = {location_groups_json};
        let activeFilter = 'all';
        let selectedShip = null;

        const cocomData = {{
            'INDOPACOM': {{ name: 'Indo-Pacific Command', lat: 15, lon: 140, regions: ['WESTPAC', 'INDOPAC', 'PACIFIC'] }},
            'CENTCOM': {{ name: 'Central Command', lat: 20, lon: 55, regions: ['CENTCOM'] }},
            'EUCOM': {{ name: 'European Command', lat: 45, lon: 10, regions: ['EUCOM'] }},
            'SOUTHCOM': {{ name: 'Southern Command', lat: 10, lon: -75, regions: ['SOUTHCOM'] }},
            'CONUS': {{ name: 'Continental U.S.', lat: 35, lon: -100, regions: ['CONUS'] }}
        }};

        const clusteredLocations = ['Norfolk / Portsmouth', 'San Diego', 'Mayport', 'Pearl Harbor', 'Yokosuka', 'Everett', 'Rota'];

        function initGlobe() {{
            const singleShips = [];
            const clusterMarkers = [];

            shipsData.forEach(ship => {{
                const shipsAtLocation = locationGroups[ship.location] || [];
                if (shipsAtLocation.length > 1 && clusteredLocations.includes(ship.location)) {{
                    if (!clusterMarkers.find(m => m.location === ship.location)) {{
                        clusterMarkers.push({{
                            location: ship.location,
                            lat: ship.lat,
                            lon: ship.lon,
                            count: shipsAtLocation.length,
                            ships: shipsAtLocation
                        }});
                    }}
                }} else {{
                    singleShips.push(ship);
                }}
            }});

            const burkeSingle = singleShips.filter(s => s.ship_class === 'Arleigh Burke');
            const zumwaltSingle = singleShips.filter(s => s.ship_class === 'Zumwalt');

            const traces = [];

            if (burkeSingle.length > 0) {{
                traces.push({{
                    type: 'scattergeo', mode: 'markers+text',
                    lat: burkeSingle.map(s => s.lat), lon: burkeSingle.map(s => s.lon),
                    text: burkeSingle.map(s => s.hull), textposition: 'top center',
                    textfont: {{ family: 'Inter, sans-serif', size: 9, color: '#ffa726', weight: 600 }},
                    hoverinfo: 'text', hovertext: burkeSingle.map(s => `<b>${{s.hull}}</b><br>${{s.name}}<br>${{s.location}}`),
                    marker: {{ size: 10, color: '#ffa726', symbol: 'circle', line: {{ width: 2, color: '#e65100' }} }},
                    name: 'Arleigh Burke-class', customdata: burkeSingle
                }});
            }}

            if (zumwaltSingle.length > 0) {{
                traces.push({{
                    type: 'scattergeo', mode: 'markers+text',
                    lat: zumwaltSingle.map(s => s.lat), lon: zumwaltSingle.map(s => s.lon),
                    text: zumwaltSingle.map(s => s.hull), textposition: 'top center',
                    textfont: {{ family: 'Inter, sans-serif', size: 9, color: '#ab47bc', weight: 600 }},
                    hoverinfo: 'text', hovertext: zumwaltSingle.map(s => `<b>${{s.hull}}</b><br>${{s.name}}<br>${{s.location}}`),
                    marker: {{ size: 10, color: '#ab47bc', symbol: 'diamond', line: {{ width: 2, color: '#7b1fa2' }} }},
                    name: 'Zumwalt-class', customdata: zumwaltSingle
                }});
            }}

            if (clusterMarkers.length > 0) {{
                traces.push({{
                    type: 'scattergeo', mode: 'markers+text',
                    lat: clusterMarkers.map(c => c.lat), lon: clusterMarkers.map(c => c.lon),
                    text: clusterMarkers.map(c => c.location + ' (' + c.count + ')'), textposition: 'top center',
                    textfont: {{ family: 'Inter, sans-serif', size: 9, color: '#00ff88', weight: 600 }},
                    hoverinfo: 'text', hovertext: clusterMarkers.map(c => `<b>${{c.location}}</b><br>${{c.count}} destroyers`),
                    marker: {{ size: 12, color: '#00ff88', symbol: 'circle', line: {{ width: 2, color: '#00cc6a' }}, opacity: 0.9 }},
                    showlegend: false, customdata: clusterMarkers.map(c => ({{ isCluster: true, ...c }}))
                }});
            }}

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
            Plotly.newPlot('globe', traces, layout, config);

            document.getElementById('globe').on('plotly_click', function(data) {{
                if (data.points && data.points.length > 0) {{
                    const pointData = data.points[0].customdata;
                    if (pointData && pointData.isCluster) {{
                        showLocationCallout(pointData, data.event);
                    }} else if (pointData) {{
                        showDetail(pointData);
                        highlightShipCard(pointData.hull);
                    }}
                }}
            }});
        }}

        function showLocationCallout(clusterData, event) {{
            const container = document.getElementById('locationCallouts');
            const mouseX = event.clientX || event.pageX || 100;
            const mouseY = event.clientY || event.pageY || 100;
            const calloutWidth = 280;
            const calloutHeight = Math.min(380, 50 + clusterData.ships.length * 28);
            const padding = 15;
            let left = mouseX + padding;
            if (left + calloutWidth > window.innerWidth - 380) {{
                left = mouseX - calloutWidth - padding;
            }}
            left = Math.max(20, left);
            let top = mouseY - calloutHeight / 2;
            top = Math.max(80, Math.min(window.innerHeight - calloutHeight - 20, top));

            let html = `<div class="location-callout" style="left: ${{left}}px; top: ${{top}}px;">
                <div class="location-callout-header">${{clusterData.location}} (${{clusterData.ships.length}} destroyers)</div>`;

            clusterData.ships.forEach(ship => {{
                const typeClass = ship.ship_class === 'Zumwalt' ? 'zumwalt' : 'burke';
                html += `<div class="location-callout-ship" onclick="selectShipFromCallout('${{ship.hull}}')" style="cursor:pointer;">
                    <div class="location-callout-icon ${{typeClass}}"></div>
                    <span class="location-callout-hull ${{typeClass}}">${{ship.hull}}</span>
                    <span class="location-callout-name">${{ship.name}}</span>
                </div>`;
            }});

            html += '</div>';
            container.innerHTML = html;

            setTimeout(() => {{
                document.addEventListener('click', closeLocationCallout, {{ once: true }});
            }}, 100);
        }}

        function closeLocationCallout() {{
            document.getElementById('locationCallouts').innerHTML = '';
        }}

        function selectShipFromCallout(hull) {{
            closeLocationCallout();
            selectShip(hull);
        }}

        function renderShipList() {{
            const container = document.getElementById('shipList');
            let filtered = shipsData;
            if (activeFilter === 'Zumwalt') {{
                filtered = shipsData.filter(s => s.ship_class === 'Zumwalt');
            }} else if (activeFilter !== 'all') {{
                filtered = shipsData.filter(s => s.flight === activeFilter);
            }}
            const grouped = {{}};
            filtered.forEach(ship => {{ if (!grouped[ship.location]) grouped[ship.location] = []; grouped[ship.location].push(ship); }});
            const sortedLocations = Object.keys(grouped).sort((a, b) => grouped[b].length - grouped[a].length);
            let html = '';
            sortedLocations.forEach(location => {{
                const ships = grouped[location];
                const count = ships.length;
                html += `<div class="location-group"><div class="location-header" onclick="rotateToLocation('${{location}}')"><span class="location-name">${{location}}</span><span class="location-count">${{count}}</span></div>`;
                ships.forEach(ship => {{
                    const typeClass = ship.ship_class === 'Zumwalt' ? 'zumwalt' : 'burke';
                    html += `<div class="ship-card ${{typeClass}}" data-hull="${{ship.hull}}" onclick="selectShip('${{ship.hull}}')"><div class="ship-header"><span class="ship-hull ${{typeClass}}">${{ship.hull}}</span><span class="ship-type">${{ship.ship_class === 'Zumwalt' ? 'DDG-1000' : 'Flight ' + ship.flight}}</span></div><div class="ship-name">${{ship.name}}</div><div class="ship-date">As of ${{ship.date}}</div></div>`;
                }});
                html += '</div>';
            }});
            container.innerHTML = html;
        }}

        function rotateToLocation(location) {{
            const ship = shipsData.find(s => s.location === location);
            if (ship) Plotly.relayout('globe', {{ 'geo.projection.rotation.lon': ship.lon, 'geo.projection.rotation.lat': Math.max(-60, Math.min(60, ship.lat)) }});
        }}

        function selectShip(hull) {{
            const ship = shipsData.find(s => s.hull === hull);
            if (ship) {{
                showDetail(ship);
                highlightShipCard(hull);
                Plotly.relayout('globe', {{ 'geo.projection.rotation.lon': ship.lon, 'geo.projection.rotation.lat': Math.max(-60, Math.min(60, ship.lat)) }});
            }}
        }}

        function highlightShipCard(hull) {{
            document.querySelectorAll('.ship-card').forEach(card => card.classList.remove('active'));
            const card = document.querySelector(`.ship-card[data-hull="${{hull}}"]`);
            if (card) {{ card.classList.add('active'); card.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }}
        }}

        function showDetail(ship) {{
            selectedShip = ship;
            document.getElementById('detailPanel').classList.remove('hidden');
            document.getElementById('detailTitle').textContent = `${{ship.hull}} - ${{ship.name}}`;
            document.getElementById('detailClass').textContent = `${{ship.ship_class}}-class`;
            document.getElementById('detailFlight').textContent = ship.ship_class === 'Zumwalt' ? 'N/A' : `Flight ${{ship.flight}}`;
            document.getElementById('detailLocation').textContent = ship.location;
            document.getElementById('detailRegion').textContent = ship.region;
            document.getElementById('detailDate').textContent = ship.date;
            document.getElementById('detailStatus').textContent = ship.status;
        }}

        function closeDetail() {{
            document.getElementById('detailPanel').classList.add('hidden');
            document.querySelectorAll('.ship-card').forEach(card => card.classList.remove('active'));
            selectedShip = null;
        }}

        function toggleCocomMenu() {{
            document.getElementById('cocomDropdown').classList.toggle('open');
        }}

        function selectCocom(cocom) {{
            document.getElementById('cocomDropdown').classList.remove('open');
            const data = cocomData[cocom];
            Plotly.relayout('globe', {{ 'geo.projection.rotation.lon': data.lon, 'geo.projection.rotation.lat': data.lat }});
            const cocomShips = shipsData.filter(s => data.regions.includes(s.region));
            document.getElementById('cocomPanelTitle').textContent = data.name + ' (' + cocomShips.length + ' ships)';
            let html = '';
            if (cocomShips.length === 0) {{
                html = '<div style="color:#666;font-size:12px;padding:10px;">No destroyers currently in this theater</div>';
            }} else {{
                cocomShips.forEach(ship => {{
                    const typeClass = ship.ship_class === 'Zumwalt' ? 'zumwalt' : 'burke';
                    html += `<div class="cocom-ship" onclick="selectShip('${{ship.hull}}')">
                        <div class="cocom-ship-icon ${{typeClass}}"></div>
                        <span class="cocom-ship-hull">${{ship.hull}}</span>
                        <span class="cocom-ship-name">${{ship.name}}</span>
                        <span class="cocom-ship-loc">${{ship.location}}</span>
                    </div>`;
                }});
            }}
            document.getElementById('cocomPanelBody').innerHTML = html;
            document.getElementById('cocomPanel').classList.add('visible');
        }}

        function closeCocomPanel() {{
            document.getElementById('cocomPanel').classList.remove('visible');
        }}

        document.addEventListener('click', function(e) {{
            if (!e.target.closest('.cocom-dropdown')) {{
                document.getElementById('cocomDropdown').classList.remove('open');
            }}
        }});

        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                activeFilter = this.dataset.filter;
                renderShipList();
            }});
        }});

        function showDDGModal() {{
            const ddgs = [...shipsData].sort((a, b) => {{
                const numA = parseInt(a.hull.replace('DDG', ''));
                const numB = parseInt(b.hull.replace('DDG', ''));
                return numA - numB;
            }});
            const grid = document.getElementById('ddgGrid');
            grid.innerHTML = ddgs.map(d => `
                <div class="ddg-item ${{d.ship_class === 'Zumwalt' ? 'zumwalt' : ''}}" onclick="selectDDGFromModal('${{d.hull}}')">
                    <div class="ddg-hull">${{d.hull}}</div>
                    <div class="ddg-name">${{d.name}}</div>
                    <div class="ddg-location">${{d.location}}</div>
                </div>
            `).join('');
            document.getElementById('ddgModal').classList.add('visible');
            document.body.style.overflow = 'hidden';
        }}

        function closeDDGModal(event) {{
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('ddgModal').classList.remove('visible');
            document.body.style.overflow = '';
        }}

        function selectDDGFromModal(hull) {{
            closeDDGModal();
            selectShip(hull);
        }}

        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                closeDDGModal();
                closeCocomPanel();
            }}
        }});

        initGlobe();
        renderShipList();
    </script>
</body>
</html>'''

    return html


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point for the scraper."""
    print("Starting U.S. Navy Destroyer Tracker...")
    print("Created by @ianellisjones and IEJ Media\n")

    # Scrape fleet data
    fleet_data = scrape_fleet()

    if not fleet_data:
        print("ERROR: No destroyer data scraped!")
        return 1

    # Generate HTML
    html_content = generate_globe_html(fleet_data)
    output_file = Path("destroyers.html")
    output_file.write_text(html_content, encoding='utf-8')
    print(f"\n>>> Destroyer tracker saved: {output_file}")

    print(f"\n    Destroyers tracked: {len(fleet_data)}")
    print(f"    Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    return 0


if __name__ == "__main__":
    exit(main())
