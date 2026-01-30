#!/usr/bin/env python3
"""
AIS SHIP LOCATION TRACKER - Marine Traffic Scraper
Version: 1.0.0

Scrapes ship location data from Marine Traffic's public pages.
Based on the transparency-everywhere/ais-api approach.

Uses only standard library - no external dependencies beyond requests.

Created for USN Fleet Tracker project
"""

import re
import json
import time
import html.parser
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

# ==============================================================================
# CONFIGURATION
# ==============================================================================

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.marinetraffic.com/',
    'Origin': 'https://www.marinetraffic.com',
    'X-Requested-With': 'XMLHttpRequest',
}

# Marine Traffic base URLs
MT_BASE_URL = 'https://www.marinetraffic.com'
MT_VESSEL_INFO = MT_BASE_URL + '/en/vesselDetails/vesselInfo/shipid:{ship_id}'
MT_LATEST_POSITION = MT_BASE_URL + '/en/vesselDetails/latestPosition/shipid:{ship_id}'
MT_VOYAGE_INFO = MT_BASE_URL + '/en/vesselDetails/voyageInfo/shipid:{ship_id}'

# Rate limiting
REQUEST_DELAY = 2  # seconds between requests

# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass
class ShipIdentifier:
    """Ship identification data"""
    ship_id: Optional[str] = None
    mmsi: Optional[str] = None
    imo: Optional[str] = None
    name: Optional[str] = None
    callsign: Optional[str] = None
    flag: Optional[str] = None
    ship_type: Optional[str] = None


@dataclass
class ShipPosition:
    """Ship position data"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed: Optional[float] = None  # knots
    course: Optional[float] = None  # degrees
    heading: Optional[float] = None  # degrees
    status: Optional[str] = None
    timestamp: Optional[str] = None
    area: Optional[str] = None


@dataclass
class ShipVoyage:
    """Ship voyage data"""
    destination: Optional[str] = None
    eta: Optional[str] = None
    draught: Optional[float] = None
    current_port: Optional[str] = None
    last_port: Optional[str] = None
    last_port_time: Optional[str] = None


@dataclass
class ShipDetails:
    """Ship physical details"""
    length: Optional[float] = None
    beam: Optional[float] = None
    gross_tonnage: Optional[int] = None
    deadweight: Optional[int] = None
    year_built: Optional[int] = None
    builder: Optional[str] = None


@dataclass
class TrackedShip:
    """Complete tracked ship data"""
    identifier: ShipIdentifier = field(default_factory=ShipIdentifier)
    position: ShipPosition = field(default_factory=ShipPosition)
    voyage: ShipVoyage = field(default_factory=ShipVoyage)
    details: ShipDetails = field(default_factory=ShipDetails)
    source_url: Optional[str] = None
    last_updated: Optional[str] = None
    tracking_link: Optional[str] = None


# ==============================================================================
# URL PARSING
# ==============================================================================

def parse_marine_traffic_url(url: str) -> Dict[str, Optional[str]]:
    """
    Parse a Marine Traffic URL to extract ship identifiers.

    Example URL:
    https://www.marinetraffic.com/en/ais/details/ships/shipid:455188/mmsi:368709000/imo:9345104/vessel:CARL%20BRASHEAR

    Returns dict with ship_id, mmsi, imo, vessel_name
    """
    result = {
        'ship_id': None,
        'mmsi': None,
        'imo': None,
        'vessel_name': None
    }

    # Extract ship_id
    ship_id_match = re.search(r'shipid[:\-](\d+)', url)
    if ship_id_match:
        result['ship_id'] = ship_id_match.group(1)

    # Extract MMSI
    mmsi_match = re.search(r'mmsi[:\-](\d+)', url)
    if mmsi_match:
        result['mmsi'] = mmsi_match.group(1)

    # Extract IMO
    imo_match = re.search(r'imo[:\-](\d+)', url)
    if imo_match:
        result['imo'] = imo_match.group(1)

    # Extract vessel name
    vessel_match = re.search(r'vessel[:\-]([^/]+)', url)
    if vessel_match:
        result['vessel_name'] = unquote(vessel_match.group(1)).replace('_', ' ')

    return result


# ==============================================================================
# SIMPLE HTML PARSER (no BeautifulSoup)
# ==============================================================================

class SimpleHTMLParser(html.parser.HTMLParser):
    """Simple HTML parser to extract text and data attributes"""

    def __init__(self):
        super().__init__()
        self.data = {}
        self.scripts = []
        self.in_script = False
        self.current_script = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.in_script = True
            self.current_script = ""

    def handle_endtag(self, tag):
        if tag == 'script' and self.in_script:
            self.in_script = False
            if self.current_script.strip():
                self.scripts.append(self.current_script)

    def handle_data(self, data):
        if self.in_script:
            self.current_script += data


def extract_json_from_html(html_content: str) -> Dict[str, Any]:
    """Extract JSON data and coordinates from HTML content using regex"""
    data = {}

    # Try to find JSON objects in script tags
    json_patterns = [
        r'var\s+shipData\s*=\s*(\{[^;]+\});',
        r'"shipData"\s*:\s*(\{[^}]+\})',
        r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?\});',
    ]

    for pattern in json_patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                data.update(json_data)
            except json.JSONDecodeError:
                pass

    # Extract coordinates from various patterns
    lat_patterns = [
        r'"lat(?:itude)?"\s*:\s*([-\d.]+)',
        r"'lat(?:itude)?'\s*:\s*([-\d.]+)",
        r'lat(?:itude)?\s*=\s*([-\d.]+)',
    ]
    lon_patterns = [
        r'"lo?n(?:gitude)?"\s*:\s*([-\d.]+)',
        r"'lo?n(?:gitude)?'\s*:\s*([-\d.]+)",
        r'lo?n(?:gitude)?\s*=\s*([-\d.]+)',
    ]

    for pattern in lat_patterns:
        match = re.search(pattern, html_content, re.I)
        if match:
            try:
                data['latitude'] = float(match.group(1))
                break
            except ValueError:
                pass

    for pattern in lon_patterns:
        match = re.search(pattern, html_content, re.I)
        if match:
            try:
                data['longitude'] = float(match.group(1))
                break
            except ValueError:
                pass

    # Extract speed
    speed_match = re.search(r'"speed"\s*:\s*([\d.]+)', html_content)
    if speed_match:
        try:
            data['speed'] = float(speed_match.group(1))
        except ValueError:
            pass

    # Extract course
    course_match = re.search(r'"course"\s*:\s*([\d.]+)', html_content)
    if course_match:
        try:
            data['course'] = float(course_match.group(1))
        except ValueError:
            pass

    return data


# ==============================================================================
# SCRAPING FUNCTIONS
# ==============================================================================

class MarineTrafficScraper:
    """Scraper for Marine Traffic ship data"""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON data from a URL"""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # Try to extract JSON from HTML response
                    return extract_json_from_html(response.text)
            else:
                print(f"  [!] HTTP {response.status_code} for {url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"  [!] Request error: {e}")
            return None

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML from a URL"""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                print(f"  [!] HTTP {response.status_code} for {url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"  [!] Request error: {e}")
            return None

    def get_ship_id_from_page(self, url: str) -> Optional[str]:
        """
        Extract ship_id from a Marine Traffic page by following redirects
        or parsing the page content.
        """
        parsed = parse_marine_traffic_url(url)
        if parsed['ship_id']:
            return parsed['ship_id']

        # Try to fetch the page and extract ship_id from redirected URL or content
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=30, allow_redirects=True)
            # Check final URL for ship_id
            final_parsed = parse_marine_traffic_url(response.url)
            if final_parsed['ship_id']:
                return final_parsed['ship_id']

            # Try to find ship_id in page content
            match = re.search(r'shipid["\']?\s*[:\-=]\s*["\']?(\d+)', response.text)
            if match:
                return match.group(1)

            return None
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error fetching page: {e}")
            return None

    def fetch_vessel_info(self, ship_id: str) -> Optional[Dict]:
        """Fetch vessel info JSON"""
        url = MT_VESSEL_INFO.format(ship_id=ship_id)
        return self._fetch_json(url)

    def fetch_latest_position(self, ship_id: str) -> Optional[Dict]:
        """Fetch latest position JSON"""
        url = MT_LATEST_POSITION.format(ship_id=ship_id)
        return self._fetch_json(url)

    def fetch_voyage_info(self, ship_id: str) -> Optional[Dict]:
        """Fetch voyage info JSON"""
        url = MT_VOYAGE_INFO.format(ship_id=ship_id)
        return self._fetch_json(url)

    def scrape_ship_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape ship data directly from the HTML page.
        Fallback method when JSON endpoints don't work.
        """
        html_content = self._fetch_html(url)
        if not html_content:
            return None

        data = extract_json_from_html(html_content)

        # Also try to extract text data using regex
        # Look for common patterns in the HTML

        # MMSI
        mmsi_match = re.search(r'MMSI[:\s]*</?\w*[^>]*>?\s*(\d{9})', html_content, re.I)
        if mmsi_match and 'mmsi' not in data:
            data['mmsi'] = mmsi_match.group(1)

        # IMO
        imo_match = re.search(r'IMO[:\s]*</?\w*[^>]*>?\s*(\d{7})', html_content, re.I)
        if imo_match and 'imo' not in data:
            data['imo'] = imo_match.group(1)

        # Flag
        flag_match = re.search(r'Flag[:\s]*</?\w*[^>]*>?\s*([A-Za-z\s]+?)(?:<|$)', html_content, re.I)
        if flag_match and 'flag' not in data:
            data['flag'] = flag_match.group(1).strip()

        return data if data else None

    def track_ship(self, url: str) -> TrackedShip:
        """
        Main method to track a ship from a Marine Traffic URL.
        Returns a TrackedShip object with all available data.
        """
        print(f"[*] Tracking ship from: {url}")

        # Parse the URL for basic identifiers
        parsed = parse_marine_traffic_url(url)

        ship = TrackedShip(
            source_url=url,
            last_updated=datetime.utcnow().isoformat() + 'Z'
        )

        # Set identifier info from URL
        ship.identifier.ship_id = parsed['ship_id']
        ship.identifier.mmsi = parsed['mmsi']
        ship.identifier.imo = parsed['imo']
        ship.identifier.name = parsed['vessel_name']

        # Try to get ship_id if not in URL
        if not ship.identifier.ship_id:
            print("  [*] Extracting ship_id from page...")
            ship.identifier.ship_id = self.get_ship_id_from_page(url)

        if ship.identifier.ship_id:
            ship_id = ship.identifier.ship_id
            print(f"  [*] Ship ID: {ship_id}")

            # Build tracking link
            ship.tracking_link = f"{MT_BASE_URL}/en/ais/details/ships/shipid:{ship_id}"

            # Try JSON endpoints
            print("  [*] Fetching vessel info...")
            vessel_info = self.fetch_vessel_info(ship_id)
            if vessel_info:
                self._parse_vessel_info(ship, vessel_info)

            print("  [*] Fetching latest position...")
            position_info = self.fetch_latest_position(ship_id)
            if position_info:
                self._parse_position_info(ship, position_info)

            print("  [*] Fetching voyage info...")
            voyage_info = self.fetch_voyage_info(ship_id)
            if voyage_info:
                self._parse_voyage_info(ship, voyage_info)

        # Fallback: scrape HTML page directly
        if not ship.position.latitude:
            print("  [*] Falling back to HTML scraping...")
            page_data = self.scrape_ship_page(url)
            if page_data:
                self._parse_page_data(ship, page_data)

        return ship

    def _parse_vessel_info(self, ship: TrackedShip, data: Dict):
        """Parse vessel info JSON into TrackedShip"""
        if not data:
            return

        # Common field mappings
        ship.identifier.name = data.get('shipName') or data.get('name') or ship.identifier.name
        ship.identifier.mmsi = data.get('mmsi') or ship.identifier.mmsi
        ship.identifier.imo = data.get('imo') or ship.identifier.imo
        ship.identifier.callsign = data.get('callsign')
        ship.identifier.flag = data.get('flag') or data.get('flagName')
        ship.identifier.ship_type = data.get('shipType') or data.get('typeName')

        ship.details.length = data.get('length')
        ship.details.beam = data.get('beam') or data.get('width')
        ship.details.gross_tonnage = data.get('grossTonnage') or data.get('gt')
        ship.details.deadweight = data.get('deadweight') or data.get('dwt')
        ship.details.year_built = data.get('yearBuilt') or data.get('buildYear')
        ship.details.builder = data.get('builder')

    def _parse_position_info(self, ship: TrackedShip, data: Dict):
        """Parse position info JSON into TrackedShip"""
        if not data:
            return

        ship.position.latitude = data.get('lat') or data.get('latitude')
        ship.position.longitude = data.get('lon') or data.get('longitude')
        ship.position.speed = data.get('speed')
        ship.position.course = data.get('course') or data.get('cog')
        ship.position.heading = data.get('heading') or data.get('hdg')
        ship.position.status = data.get('status') or data.get('navStatus')
        ship.position.timestamp = data.get('timestamp') or data.get('lastPos')
        ship.position.area = data.get('area') or data.get('location')

    def _parse_voyage_info(self, ship: TrackedShip, data: Dict):
        """Parse voyage info JSON into TrackedShip"""
        if not data:
            return

        ship.voyage.destination = data.get('destination')
        ship.voyage.eta = data.get('eta')
        ship.voyage.draught = data.get('draught') or data.get('draft')
        ship.voyage.current_port = data.get('currentPort') or data.get('port')
        ship.voyage.last_port = data.get('lastPort')
        ship.voyage.last_port_time = data.get('lastPortTime')

    def _parse_page_data(self, ship: TrackedShip, data: Dict):
        """Parse HTML-scraped data into TrackedShip"""
        if not data:
            return

        # Direct assignments
        if 'latitude' in data:
            ship.position.latitude = data['latitude']
        if 'longitude' in data:
            ship.position.longitude = data['longitude']
        if 'speed' in data:
            ship.position.speed = data['speed']
        if 'course' in data:
            ship.position.course = data['course']
        if 'mmsi' in data and not ship.identifier.mmsi:
            ship.identifier.mmsi = str(data['mmsi'])
        if 'imo' in data and not ship.identifier.imo:
            ship.identifier.imo = str(data['imo'])
        if 'flag' in data and not ship.identifier.flag:
            ship.identifier.flag = data['flag']


# ==============================================================================
# SHIP DATABASE - Ships to Track
# ==============================================================================

# List of ships to track with their Marine Traffic URLs
TRACKED_SHIPS = [
    # Example ships - add your ships here
    {
        "name": "USNS Carl Brashear",
        "hull": "T-AKE-7",
        "url": "https://www.marinetraffic.com/en/ais/details/ships/shipid:455188/mmsi:368709000/imo:9345104/vessel:CARL%20BRASHEAR"
    },
    {
        "name": "USNS Henry J. Kaiser",
        "hull": "T-AO-187",
        "url": "https://www.marinetraffic.com/en/ais/details/ships/shipid:359098/mmsi:303849000/imo:8302416/vessel:HENRY_J_KAISER"
    },
]


# ==============================================================================
# OUTPUT GENERATION
# ==============================================================================

def ship_to_dict(ship: TrackedShip) -> Dict:
    """Convert TrackedShip to a serializable dictionary"""
    return {
        'identifier': asdict(ship.identifier),
        'position': asdict(ship.position),
        'voyage': asdict(ship.voyage),
        'details': asdict(ship.details),
        'source_url': ship.source_url,
        'last_updated': ship.last_updated,
        'tracking_link': ship.tracking_link
    }


def generate_json_output(ships: List[TrackedShip], output_file: str = 'ais_data.json'):
    """Generate JSON file with all tracked ship data"""
    data = {
        'generated': datetime.utcnow().isoformat() + 'Z',
        'ship_count': len(ships),
        'ships': [ship_to_dict(ship) for ship in ships]
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[+] Generated {output_file}")


def generate_html_output(ships: List[TrackedShip], output_file: str = 'ais_tracker.html'):
    """Generate HTML page displaying tracked ships"""

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIS Ship Tracker</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            margin-bottom: 30px;
            border-bottom: 1px solid #333;
        }}
        .header h1 {{
            color: #00d4ff;
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .header .timestamp {{
            color: #888;
            font-size: 0.9rem;
        }}
        .ships-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .ship-card {{
            background: #141420;
            border: 1px solid #2a2a3a;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .ship-card:hover {{
            transform: translateY(-2px);
            border-color: #00d4ff;
        }}
        .ship-name {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 5px;
        }}
        .ship-type {{
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }}
        .ship-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}
        .detail-item {{
            background: #1a1a2a;
            padding: 10px;
            border-radius: 8px;
        }}
        .detail-label {{
            color: #666;
            font-size: 0.75rem;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .detail-value {{
            color: #fff;
            font-size: 0.95rem;
            font-weight: 500;
        }}
        .position-value {{
            color: #00ff88;
        }}
        .detail-item.full-width {{
            grid-column: span 2;
        }}
        .track-link {{
            display: block;
            margin-top: 15px;
            padding: 10px;
            background: #00d4ff22;
            border: 1px solid #00d4ff44;
            border-radius: 8px;
            color: #00d4ff;
            text-decoration: none;
            text-align: center;
            transition: background 0.2s;
        }}
        .track-link:hover {{
            background: #00d4ff33;
        }}
        .no-data {{
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AIS Ship Tracker</h1>
        <div class="timestamp">Last Updated: {timestamp}</div>
    </div>

    <div class="ships-grid">
        {ship_cards}
    </div>
</body>
</html>'''

    card_template = '''
        <div class="ship-card">
            <div class="ship-name">{name}</div>
            <div class="ship-type">{ship_type} | {flag}</div>
            <div class="ship-details">
                <div class="detail-item">
                    <div class="detail-label">MMSI</div>
                    <div class="detail-value">{mmsi}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">IMO</div>
                    <div class="detail-value">{imo}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Position</div>
                    <div class="detail-value position-value">{position}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Speed</div>
                    <div class="detail-value">{speed}</div>
                </div>
                <div class="detail-item full-width">
                    <div class="detail-label">Destination</div>
                    <div class="detail-value">{destination}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Last Update</div>
                    <div class="detail-value">{last_update}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">{status}</div>
                </div>
            </div>
            <a href="{tracking_link}" target="_blank" class="track-link">View Live Track</a>
        </div>'''

    ship_cards = []
    for ship in ships:
        # Format position
        if ship.position.latitude and ship.position.longitude:
            position = f"{ship.position.latitude:.4f}, {ship.position.longitude:.4f}"
        else:
            position = '<span class="no-data">Unknown</span>'

        # Format speed
        if ship.position.speed is not None:
            speed = f"{ship.position.speed} kn"
        else:
            speed = '<span class="no-data">--</span>'

        card = card_template.format(
            name=ship.identifier.name or 'Unknown Vessel',
            ship_type=ship.identifier.ship_type or 'Unknown Type',
            flag=ship.identifier.flag or 'Unknown Flag',
            mmsi=ship.identifier.mmsi or '--',
            imo=ship.identifier.imo or '--',
            position=position,
            speed=speed,
            destination=ship.voyage.destination or '<span class="no-data">Not reported</span>',
            last_update=ship.position.timestamp or ship.last_updated or '--',
            status=ship.position.status or '<span class="no-data">Unknown</span>',
            tracking_link=ship.tracking_link or ship.source_url or '#'
        )
        ship_cards.append(card)

    html = html_template.format(
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        ship_cards='\n'.join(ship_cards)
    )

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"[+] Generated {output_file}")


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main function to track ships and generate output"""
    print("=" * 60)
    print("AIS SHIP TRACKER")
    print("=" * 60)
    print()

    scraper = MarineTrafficScraper()
    tracked_ships = []

    for ship_entry in TRACKED_SHIPS:
        print(f"\n{'='*60}")
        print(f"Tracking: {ship_entry['name']} ({ship_entry.get('hull', 'N/A')})")
        print(f"{'='*60}")

        try:
            ship = scraper.track_ship(ship_entry['url'])

            # Override name with our known name if scraping didn't get it
            if not ship.identifier.name:
                ship.identifier.name = ship_entry['name']

            tracked_ships.append(ship)

            # Print summary
            print(f"\n  Summary:")
            print(f"    Name: {ship.identifier.name}")
            print(f"    MMSI: {ship.identifier.mmsi}")
            print(f"    IMO: {ship.identifier.imo}")
            print(f"    Flag: {ship.identifier.flag}")
            if ship.position.latitude and ship.position.longitude:
                print(f"    Position: {ship.position.latitude}, {ship.position.longitude}")
            else:
                print(f"    Position: Unknown")
            print(f"    Speed: {ship.position.speed} kn" if ship.position.speed else "    Speed: Unknown")
            print(f"    Destination: {ship.voyage.destination or 'Unknown'}")

        except Exception as e:
            print(f"  [!] Error tracking ship: {e}")

    print(f"\n{'='*60}")
    print(f"GENERATING OUTPUT")
    print(f"{'='*60}")

    # Generate outputs
    generate_json_output(tracked_ships)
    generate_html_output(tracked_ships)

    print(f"\n[+] Tracked {len(tracked_ships)} ships successfully")


if __name__ == '__main__':
    main()
