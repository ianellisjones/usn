#!/usr/bin/env python3
"""
U.S. NAVY DVIDS NEWS AGGREGATOR
Version: 2.2.0

Scrapes weekly news, images, and videos from DVIDS (Defense Visual Information Distribution Service)
and generates a modern web interface sorted by Combatant Command and geography/location.
Features toggle between Daily (24h) and Weekly (7-day) views.
Highlights deployment-related content with special tags.

For use in Google Colab or GitHub Actions automation.

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

import requests

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# DVIDS API Configuration
# Get your free API key at: https://api.dvidshub.net/docs (click signup in top right)
DVIDS_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key
DVIDS_API_BASE = "https://api.dvidshub.net"

# Content types to fetch
CONTENT_TYPES = ["news", "image", "video"]

# Military branches to focus on (Navy-related)
BRANCHES = ["Navy", "Marines", "Coast Guard", "Joint"]

# Maximum results per query
MAX_RESULTS_PER_QUERY = 100

# Lookback period in days (7 days = 1 week)
LOOKBACK_DAYS = 7

# User agent for requests
USER_AGENT = 'DVIDS-News-Aggregator/2.2 (Python; +https://github.com/ianellisjones/usn)'

# ==============================================================================
# COMBATANT COMMAND KEYWORDS
# ==============================================================================

COMMAND_KEYWORDS = {
    "INDOPACOM": ["INDOPACOM", "U.S. Indo-Pacific Command", "Indo-Pacific Command"],
    "CENTCOM": ["CENTCOM", "U.S. Central Command", "Central Command"],
    "SOUTHCOM": ["SOUTHCOM", "U.S. Southern Command", "Southern Command"],
    "EUCOM": ["EUCOM", "U.S. European Command", "European Command"],
}

# ==============================================================================
# DEPLOYMENT KEYWORDS
# ==============================================================================

DEPLOYMENT_KEYWORDS = ["deploy", "deploys", "deployed", "deployment"]

# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class DVIDSItem:
    """Data class representing a DVIDS content item."""
    id: str
    title: str
    description: str
    type: str  # news, image, video
    branch: str
    unit_name: str
    date_published: str
    timestamp: str  # ISO format for sorting
    country: str
    state: str
    city: str
    location_display: str
    url: str
    thumbnail_url: str
    keywords: List[str] = field(default_factory=list)
    credit: str = ""
    duration: str = ""  # For videos
    aspect_ratio: str = ""
    commands: List[str] = field(default_factory=list)  # Combatant commands detected
    hours_old: float = 0.0  # Hours since publication (for daily/weekly filtering)
    is_deployment: bool = False  # Whether this item is deployment-related


@dataclass
class DailyDigest:
    """Data class for a day's/week's worth of DVIDS content."""
    date: str
    items: List[DVIDSItem]
    total_count: int
    by_country: Dict[str, int]
    by_type: Dict[str, int]
    by_branch: Dict[str, int]
    by_command: Dict[str, int] = field(default_factory=dict)  # Items by combatant command
    deployment_count: int = 0  # Number of deployment-related items


# ==============================================================================
# LOCATION MAPPING
# ==============================================================================

# Map country codes to full names
COUNTRY_NAMES = {
    "US": "United States",
    "JP": "Japan",
    "KR": "South Korea",
    "PH": "Philippines",
    "AU": "Australia",
    "DE": "Germany",
    "IT": "Italy",
    "ES": "Spain",
    "UK": "United Kingdom",
    "GB": "United Kingdom",
    "BH": "Bahrain",
    "AE": "United Arab Emirates",
    "QA": "Qatar",
    "KW": "Kuwait",
    "DJ": "Djibouti",
    "GR": "Greece",
    "TR": "Turkey",
    "PL": "Poland",
    "NO": "Norway",
    "SE": "Sweden",
    "FI": "Finland",
    "IS": "Iceland",
    "CA": "Canada",
    "MX": "Mexico",
    "PR": "Puerto Rico",
    "GU": "Guam",
    "VI": "U.S. Virgin Islands",
    "CU": "Cuba (Guantanamo Bay)",
    "SG": "Singapore",
    "TH": "Thailand",
    "VN": "Vietnam",
    "IN": "India",
    "PK": "Pakistan",
    "AF": "Afghanistan",
    "IQ": "Iraq",
    "SY": "Syria",
    "JO": "Jordan",
    "IL": "Israel",
    "EG": "Egypt",
    "SA": "Saudi Arabia",
    "OM": "Oman",
    "YE": "Yemen",
}

# Region groupings for geographic organization
REGION_MAP = {
    "United States": "CONUS",
    "Puerto Rico": "Caribbean",
    "U.S. Virgin Islands": "Caribbean",
    "Cuba (Guantanamo Bay)": "Caribbean",
    "Guam": "Indo-Pacific",
    "Japan": "Indo-Pacific",
    "South Korea": "Indo-Pacific",
    "Philippines": "Indo-Pacific",
    "Australia": "Indo-Pacific",
    "Singapore": "Indo-Pacific",
    "Thailand": "Indo-Pacific",
    "Vietnam": "Indo-Pacific",
    "India": "Indo-Pacific",
    "Germany": "Europe",
    "Italy": "Europe",
    "Spain": "Europe",
    "United Kingdom": "Europe",
    "Greece": "Europe",
    "Turkey": "Europe",
    "Poland": "Europe",
    "Norway": "Europe",
    "Sweden": "Europe",
    "Finland": "Europe",
    "Iceland": "Europe",
    "Bahrain": "Middle East",
    "United Arab Emirates": "Middle East",
    "Qatar": "Middle East",
    "Kuwait": "Middle East",
    "Saudi Arabia": "Middle East",
    "Oman": "Middle East",
    "Iraq": "Middle East",
    "Syria": "Middle East",
    "Jordan": "Middle East",
    "Israel": "Middle East",
    "Egypt": "Middle East",
    "Yemen": "Middle East",
    "Djibouti": "Africa",
    "Afghanistan": "Central Asia",
    "Pakistan": "Central Asia",
    "Canada": "North America",
    "Mexico": "Central America",
}


# ==============================================================================
# API FUNCTIONS
# ==============================================================================

def make_api_request(endpoint: str, params: Dict, retries: int = 3) -> Optional[Dict]:
    """Make a request to the DVIDS API with retry logic."""
    url = f"{DVIDS_API_BASE}{endpoint}"
    params["api_key"] = DVIDS_API_KEY

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"  ERROR: API key invalid or missing. Get one at https://api.dvidshub.net/docs")
                return None
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = 2 ** attempt
                print(f"  Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"  HTTP {response.status_code}: {response.text[:200]}")

        except requests.RequestException as e:
            print(f"  Request error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)

    return None


def search_dvids(
    content_type: str = "news",
    branch: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_results: int = 50,
    sort: str = "date"
) -> List[Dict]:
    """
    Search DVIDS for content.

    Args:
        content_type: Type of content (news, image, video)
        branch: Military branch filter
        from_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        to_date: End date in ISO format
        max_results: Maximum number of results to return
        sort: Sort order (date, rating, title)

    Returns:
        List of content items from DVIDS
    """
    params = {
        "type": content_type,
        "max_results": min(max_results, MAX_RESULTS_PER_QUERY),
        "sort": sort,
    }

    if branch:
        params["branch"] = branch
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date

    result = make_api_request("/search", params)

    if result and "results" in result:
        return result["results"]

    return []


def get_asset_details(asset_id: str, asset_type: str) -> Optional[Dict]:
    """Get detailed information about a specific asset."""
    params = {"id": asset_id}
    result = make_api_request(f"/{asset_type}", params)

    if result and "results" in result and len(result["results"]) > 0:
        return result["results"][0]

    return None


# ==============================================================================
# DATA PROCESSING
# ==============================================================================

def detect_commands(text: str) -> List[str]:
    """Detect combatant command keywords in text."""
    if not text:
        return []

    detected = []
    text_upper = text.upper()

    for command, keywords in COMMAND_KEYWORDS.items():
        for keyword in keywords:
            if keyword.upper() in text_upper:
                if command not in detected:
                    detected.append(command)
                break

    return detected


def detect_deployment(text: str) -> bool:
    """Detect deployment-related keywords in text."""
    if not text:
        return False

    text_lower = text.lower()
    for keyword in DEPLOYMENT_KEYWORDS:
        if keyword.lower() in text_lower:
            return True

    return False


def parse_dvids_item(raw_item: Dict) -> Optional[DVIDSItem]:
    """Parse a raw DVIDS API result into a DVIDSItem."""
    try:
        # Extract basic fields
        item_id = str(raw_item.get("id", ""))
        title = raw_item.get("title", "Untitled")
        description = raw_item.get("description", raw_item.get("short_description", ""))
        content_type = raw_item.get("type", "unknown")

        # Clean up description
        if description:
            description = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
            description = description[:500] + "..." if len(description) > 500 else description

        # Branch and unit
        branch = raw_item.get("branch", "Unknown")
        unit_name = raw_item.get("unit_name", "Unknown Unit")

        # Date handling
        date_published = raw_item.get("date_published", raw_item.get("date", ""))
        hours_old = 0.0
        if date_published:
            # Convert to consistent format
            try:
                if "T" in date_published:
                    dt = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(date_published[:10], "%Y-%m-%d")
                timestamp = dt.isoformat()
                date_published = dt.strftime("%b %d, %Y %H:%M UTC")
                # Calculate hours since publication
                now = datetime.utcnow()
                if dt.tzinfo:
                    dt_naive = dt.replace(tzinfo=None)
                else:
                    dt_naive = dt
                hours_old = (now - dt_naive).total_seconds() / 3600.0
            except (ValueError, TypeError):
                timestamp = ""
                date_published = str(date_published)
        else:
            timestamp = ""
            date_published = "Unknown Date"

        # Location data
        country_code = raw_item.get("country", "")
        country = COUNTRY_NAMES.get(country_code, country_code) if country_code else "Unknown"
        state = raw_item.get("state", "")
        city = raw_item.get("city", "")

        # Build display location
        location_parts = []
        if city:
            location_parts.append(city)
        if state and country == "United States":
            location_parts.append(state)
        if country and country != "Unknown":
            location_parts.append(country)
        location_display = ", ".join(location_parts) if location_parts else "Location Unknown"

        # URLs
        url = raw_item.get("url", f"https://www.dvidshub.net/{content_type}/{item_id}")
        thumbnail_url = raw_item.get("thumbnail", raw_item.get("thumbnail_url", ""))

        # Additional metadata
        keywords = raw_item.get("keywords", "").split(",") if raw_item.get("keywords") else []
        keywords = [k.strip() for k in keywords if k.strip()]

        credit = raw_item.get("credit", raw_item.get("author", ""))
        duration = raw_item.get("duration", "")
        aspect_ratio = raw_item.get("aspect_ratio", "")

        # Detect combatant commands in title, description, and unit name
        search_text = f"{title} {description} {unit_name}"
        commands = detect_commands(search_text)

        # Detect deployment-related content
        is_deployment = detect_deployment(search_text)

        return DVIDSItem(
            id=item_id,
            title=title,
            description=description,
            type=content_type,
            branch=branch,
            unit_name=unit_name,
            date_published=date_published,
            timestamp=timestamp,
            country=country,
            state=state,
            city=city,
            location_display=location_display,
            url=url,
            thumbnail_url=thumbnail_url,
            keywords=keywords,
            credit=credit,
            duration=duration,
            aspect_ratio=aspect_ratio,
            commands=commands,
            hours_old=hours_old,
            is_deployment=is_deployment,
        )

    except Exception as e:
        print(f"  Error parsing item: {e}")
        return None


def fetch_daily_content(
    date: Optional[datetime] = None,
    lookback_days: int = LOOKBACK_DAYS,
    branches: List[str] = None
) -> List[DVIDSItem]:
    """
    Fetch all Navy-related content from the past N days.

    Args:
        date: Reference date (defaults to now)
        lookback_days: How many days back to search
        branches: List of branches to include

    Returns:
        List of DVIDSItem objects
    """
    if date is None:
        date = datetime.utcnow()

    if branches is None:
        branches = BRANCHES

    # Calculate date range
    to_date = date.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_date = (date - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n{'='*70}")
    print(f"  DVIDS WEEKLY DIGEST - FETCHING CONTENT")
    print(f"  Time Range: {from_date} to {to_date}")
    print(f"  ({lookback_days} days)")
    print(f"{'='*70}\n")

    all_items = []
    seen_ids = set()

    for branch in branches:
        for content_type in CONTENT_TYPES:
            print(f"  Fetching {branch} {content_type}...", end=" ")

            results = search_dvids(
                content_type=content_type,
                branch=branch,
                from_date=from_date,
                to_date=to_date,
                max_results=MAX_RESULTS_PER_QUERY,
                sort="date"
            )

            count = 0
            for raw_item in results:
                item = parse_dvids_item(raw_item)
                if item and item.id not in seen_ids:
                    seen_ids.add(item.id)
                    all_items.append(item)
                    count += 1

            print(f"{count} items")
            time.sleep(0.5)  # Rate limiting

    # Sort by timestamp (most recent first)
    all_items.sort(key=lambda x: x.timestamp, reverse=True)

    print(f"\n  Total unique items: {len(all_items)}")
    print(f"{'='*70}\n")

    return all_items


def create_daily_digest(items: List[DVIDSItem], date_str: str = None) -> DailyDigest:
    """Create a DailyDigest summary from a list of items."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Count by category
    by_country = defaultdict(int)
    by_type = defaultdict(int)
    by_branch = defaultdict(int)
    by_command = defaultdict(int)
    deployment_count = 0

    for item in items:
        by_country[item.country] += 1
        by_type[item.type] += 1
        by_branch[item.branch] += 1
        for cmd in item.commands:
            by_command[cmd] += 1
        if item.is_deployment:
            deployment_count += 1

    return DailyDigest(
        date=date_str,
        items=items,
        total_count=len(items),
        by_country=dict(by_country),
        by_type=dict(by_type),
        by_branch=dict(by_branch),
        by_command=dict(by_command),
        deployment_count=deployment_count,
    )


# ==============================================================================
# HTML GENERATION
# ==============================================================================

def generate_dvids_html(digest: DailyDigest) -> str:
    """Generate the DVIDS News HTML page."""

    items_json = json.dumps([asdict(item) for item in digest.items])
    by_country_json = json.dumps(digest.by_country)
    by_type_json = json.dumps(digest.by_type)
    by_branch_json = json.dumps(digest.by_branch)
    by_command_json = json.dumps(digest.by_command)
    deployment_count = digest.deployment_count

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Calculate date range for display
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

    # Count summaries
    news_count = digest.by_type.get("news", 0)
    image_count = digest.by_type.get("image", 0)
    video_count = digest.by_type.get("video", 0)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DVIDS DIGEST - U.S. Navy News</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0f; color: #e0e0e0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; min-height: 100vh; }}

        /* Header */
        .header {{ background: linear-gradient(180deg, #111118 0%, #0a0a0f 100%); border-bottom: 1px solid #1e1e2e; padding: 16px 24px; position: sticky; top: 0; z-index: 100; }}
        .header-content {{ max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
        .header-left {{ display: flex; align-items: center; gap: 20px; }}
        .logo {{ font-size: 18px; font-weight: 700; color: #00ff88; letter-spacing: 1px; }}
        .logo-sub {{ font-size: 10px; font-weight: 500; color: #666; letter-spacing: 2px; margin-top: 2px; text-transform: uppercase; }}
        .stats-bar {{ display: flex; gap: 24px; flex-wrap: wrap; }}
        .stat {{ text-align: center; padding: 8px 16px; background: rgba(255,255,255,0.02); border-radius: 8px; }}
        .stat-value {{ font-size: 24px; font-weight: 700; }}
        .stat-value.total {{ color: #00ffff; }}
        .stat-value.news {{ color: #ff6b6b; }}
        .stat-value.image {{ color: #4ecdc4; }}
        .stat-value.video {{ color: #ffd93d; }}
        .stat-label {{ font-size: 9px; font-weight: 600; color: #555; letter-spacing: 1px; text-transform: uppercase; margin-top: 2px; }}
        .timestamp {{ font-size: 11px; color: #444; font-weight: 500; }}
        .timestamp span {{ color: #00ff88; }}

        /* Time Range Toggle */
        .toggle-container {{ display: flex; align-items: center; gap: 12px; }}
        .toggle-label {{ font-size: 10px; font-weight: 600; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
        .toggle-switch {{ display: flex; background: rgba(255,255,255,0.05); border: 1px solid #2a2a3a; border-radius: 8px; overflow: hidden; }}
        .toggle-btn {{ font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; padding: 8px 16px; background: transparent; border: none; color: #666; cursor: pointer; transition: all 0.15s; }}
        .toggle-btn:hover {{ color: #aaa; }}
        .toggle-btn.active {{ background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); color: #000; }}
        .toggle-btn.active:hover {{ color: #000; }}

        /* Main Layout */
        .main-container {{ max-width: 1400px; margin: 0 auto; padding: 20px; display: grid; grid-template-columns: 280px 1fr; gap: 20px; }}

        /* Sidebar */
        .sidebar {{ background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 12px; padding: 16px; height: fit-content; position: sticky; top: 100px; }}
        .sidebar-title {{ font-size: 11px; font-weight: 600; color: #00ff88; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 16px; }}
        .filter-section {{ margin-bottom: 20px; }}
        .filter-label {{ font-size: 10px; font-weight: 600; color: #666; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }}
        .filter-group {{ display: flex; flex-direction: column; gap: 6px; }}
        .filter-btn {{ font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 500; padding: 8px 12px; background: transparent; border: 1px solid #2a2a3a; color: #888; cursor: pointer; border-radius: 6px; transition: all 0.15s; text-align: left; display: flex; justify-content: space-between; align-items: center; }}
        .filter-btn:hover {{ border-color: #444; color: #ccc; }}
        .filter-btn.active {{ background: rgba(0, 255, 136, 0.1); border-color: #00ff88; color: #00ff88; }}
        .filter-count {{ font-size: 10px; color: #555; }}
        .filter-btn.active .filter-count {{ color: #00ff88; }}

        /* Search */
        .search-box {{ margin-bottom: 16px; }}
        .search-input {{ width: 100%; padding: 10px 12px; background: rgba(255,255,255,0.02); border: 1px solid #2a2a3a; border-radius: 8px; color: #e0e0e0; font-family: 'Inter', sans-serif; font-size: 12px; }}
        .search-input:focus {{ outline: none; border-color: #00ff88; }}
        .search-input::placeholder {{ color: #555; }}

        /* Content Area */
        .content-area {{ min-height: 80vh; }}
        .content-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
        .results-count {{ font-size: 12px; color: #888; }}

        /* Section Groups */
        .section-group {{ margin-bottom: 32px; }}
        .section-title {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #1e1e2e; }}
        .section-title.command {{ color: #ff6b6b; border-bottom-color: #ff6b6b; }}
        .section-title.geography {{ color: #00ff88; border-bottom-color: #00ff88; }}

        /* Location Groups */
        .location-group {{ margin-bottom: 24px; }}
        .location-header {{ display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: rgba(0, 255, 136, 0.05); border-radius: 10px; margin-bottom: 12px; cursor: pointer; }}
        .location-header:hover {{ background: rgba(0, 255, 136, 0.08); }}
        .region-badge {{ font-size: 9px; font-weight: 600; color: #00ffff; background: rgba(0, 255, 255, 0.1); padding: 3px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .location-name {{ flex: 1; font-size: 14px; font-weight: 600; color: #00ff88; }}
        .location-count {{ font-size: 11px; font-weight: 600; color: #888; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 12px; }}

        /* Item Cards */
        .items-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; padding-left: 12px; }}
        .item-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid #1e1e2e; border-radius: 12px; overflow: hidden; transition: all 0.2s; cursor: pointer; }}
        .item-card:hover {{ border-color: #333; background: rgba(255, 255, 255, 0.04); transform: translateY(-2px); }}
        .item-card.news {{ border-left: 4px solid #ff6b6b; }}
        .item-card.image {{ border-left: 4px solid #4ecdc4; }}
        .item-card.video {{ border-left: 4px solid #ffd93d; }}

        .item-thumbnail {{ width: 100%; height: 160px; object-fit: cover; background: #1a1a2e; }}
        .item-content {{ padding: 14px 16px; }}
        .item-meta {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
        .item-type {{ font-size: 9px; font-weight: 600; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .item-type.news {{ background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }}
        .item-type.image {{ background: rgba(78, 205, 196, 0.15); color: #4ecdc4; }}
        .item-type.video {{ background: rgba(255, 217, 61, 0.15); color: #ffd93d; }}
        .deployment-tag {{ font-size: 8px; font-weight: 700; padding: 3px 6px; border-radius: 4px; background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: #000; text-transform: uppercase; letter-spacing: 0.5px; margin-left: 6px; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} }}
        .item-branch {{ font-size: 10px; color: #666; font-weight: 500; }}
        .item-title {{ font-size: 14px; font-weight: 600; color: #fff; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .item-description {{ font-size: 12px; color: #888; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 10px; }}
        .item-footer {{ display: flex; justify-content: space-between; align-items: center; }}
        .item-unit {{ font-size: 10px; color: #555; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .item-date {{ font-size: 10px; color: #444; }}

        /* List View */
        .items-list {{ display: flex; flex-direction: column; gap: 8px; padding-left: 12px; }}
        .item-row {{ display: flex; align-items: center; gap: 16px; background: rgba(255, 255, 255, 0.02); border: 1px solid #1e1e2e; border-radius: 8px; padding: 12px 16px; cursor: pointer; transition: all 0.15s; }}
        .item-row:hover {{ border-color: #333; background: rgba(255, 255, 255, 0.04); }}
        .item-row.news {{ border-left: 3px solid #ff6b6b; }}
        .item-row.image {{ border-left: 3px solid #4ecdc4; }}
        .item-row.video {{ border-left: 3px solid #ffd93d; }}
        .item-row-type {{ width: 60px; flex-shrink: 0; }}
        .item-row-main {{ flex: 1; min-width: 0; }}
        .item-row-title {{ font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .item-row-unit {{ font-size: 11px; color: #666; margin-top: 2px; }}
        .item-row-meta {{ display: flex; gap: 16px; flex-shrink: 0; text-align: right; }}
        .item-row-branch {{ font-size: 10px; color: #888; }}
        .item-row-date {{ font-size: 10px; color: #555; }}

        /* Detail Modal */
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.9); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; visibility: hidden; transition: all 0.3s ease; padding: 20px; }}
        .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
        .modal {{ background: #111118; border: 1px solid #2a2a3a; border-radius: 16px; width: 100%; max-width: 800px; max-height: 90vh; overflow: hidden; transform: scale(0.9); transition: transform 0.3s ease; }}
        .modal-overlay.visible .modal {{ transform: scale(1); }}
        .modal-header {{ padding: 20px 24px; border-bottom: 1px solid #1e1e2e; display: flex; justify-content: space-between; align-items: flex-start; }}
        .modal-title {{ font-size: 18px; font-weight: 700; color: #fff; line-height: 1.4; flex: 1; padding-right: 16px; }}
        .modal-close {{ cursor: pointer; color: #555; font-size: 28px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; flex-shrink: 0; }}
        .modal-close:hover {{ color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }}
        .modal-body {{ padding: 24px; overflow-y: auto; max-height: calc(90vh - 180px); }}
        .modal-image {{ width: 100%; max-height: 400px; object-fit: contain; background: #0a0a0f; border-radius: 8px; margin-bottom: 20px; }}
        .modal-meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }}
        .modal-tag {{ font-size: 11px; font-weight: 500; padding: 6px 12px; border-radius: 6px; background: rgba(255,255,255,0.05); color: #888; }}
        .modal-tag.type {{ color: #00ffff; background: rgba(0, 255, 255, 0.1); }}
        .modal-tag.branch {{ color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }}
        .modal-tag.location {{ color: #00ff88; background: rgba(0, 255, 136, 0.1); }}
        .modal-description {{ font-size: 14px; color: #ccc; line-height: 1.7; margin-bottom: 20px; }}
        .modal-info {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }}
        .modal-info-item {{ background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; }}
        .modal-info-label {{ font-size: 10px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .modal-info-value {{ font-size: 13px; color: #aaa; }}
        .modal-footer {{ padding: 16px 24px; border-top: 1px solid #1e1e2e; display: flex; justify-content: flex-end; gap: 12px; }}
        .modal-btn {{ font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.15s; }}
        .modal-btn.primary {{ background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); color: #000; }}
        .modal-btn.primary:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3); }}

        /* Empty State */
        .empty-state {{ text-align: center; padding: 60px 20px; color: #555; }}
        .empty-state-icon {{ font-size: 48px; margin-bottom: 16px; }}
        .empty-state-title {{ font-size: 18px; font-weight: 600; color: #888; margin-bottom: 8px; }}
        .empty-state-text {{ font-size: 13px; }}

        /* Attribution */
        .attribution {{ text-align: center; padding: 24px; font-size: 10px; color: #444; }}

        /* Mobile Responsive */
        @media (max-width: 900px) {{
            .main-container {{ grid-template-columns: 1fr; }}
            .sidebar {{ position: static; }}
            .header-content {{ flex-direction: column; align-items: flex-start; }}
            .stats-bar {{ width: 100%; justify-content: space-between; }}
        }}

        @media (max-width: 600px) {{
            .items-grid {{ grid-template-columns: 1fr; }}
            .modal {{ border-radius: 16px 16px 0 0; max-height: 95vh; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="header-left">
                <div>
                    <div class="logo" id="digestTitle">DVIDS DAILY DIGEST</div>
                    <div class="logo-sub" id="digestSubtitle">U.S. Navy &amp; Marine Corps News | Last 24 Hours</div>
                </div>
            </div>
            <div class="toggle-container">
                <span class="toggle-label">View</span>
                <div class="toggle-switch">
                    <button class="toggle-btn active" id="dailyBtn" onclick="setTimeRange('daily')">Daily</button>
                    <button class="toggle-btn" id="weeklyBtn" onclick="setTimeRange('weekly')">Weekly</button>
                </div>
            </div>
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-value total" id="statTotal">{digest.total_count}</div>
                    <div class="stat-label">Total Items</div>
                </div>
                <div class="stat">
                    <div class="stat-value news" id="statNews">{news_count}</div>
                    <div class="stat-label">News</div>
                </div>
                <div class="stat">
                    <div class="stat-value image" id="statImages">{image_count}</div>
                    <div class="stat-label">Images</div>
                </div>
                <div class="stat">
                    <div class="stat-value video" id="statVideos">{video_count}</div>
                    <div class="stat-label">Videos</div>
                </div>
            </div>
            <div class="timestamp">
                Last Update: <span>{timestamp}</span>
            </div>
        </div>
    </header>

    <div class="main-container">
        <aside class="sidebar">
            <div class="sidebar-title">Filters</div>

            <div class="search-box">
                <input type="text" class="search-input" id="searchInput" placeholder="Search titles, units..." oninput="filterItems()">
            </div>

            <div class="filter-section">
                <div class="filter-label">Content Type</div>
                <div class="filter-group" id="typeFilters"></div>
            </div>

            <div class="filter-section">
                <div class="filter-label">Deployments</div>
                <div class="filter-group" id="deploymentFilters"></div>
            </div>

            <div class="filter-section">
                <div class="filter-label">Combatant Command</div>
                <div class="filter-group" id="commandFilters"></div>
            </div>

            <div class="filter-section">
                <div class="filter-label">Branch</div>
                <div class="filter-group" id="branchFilters"></div>
            </div>

            <div class="filter-section">
                <div class="filter-label">Country</div>
                <div class="filter-group" id="countryFilters"></div>
            </div>
        </aside>

        <main class="content-area">
            <div class="content-header">
                <div class="results-count" id="resultsCount">Showing {digest.total_count} items</div>
            </div>
            <div id="contentContainer"></div>
        </main>
    </div>

    <div class="attribution">
        Created by @ianellisjones and IEJ Media | Data from DVIDS (dvidshub.net)
    </div>

    <div class="modal-overlay" id="detailModal" onclick="closeModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">-</div>
                <span class="modal-close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body" id="modalBody"></div>
            <div class="modal-footer">
                <a id="modalLink" href="#" target="_blank" rel="noopener">
                    <button class="modal-btn primary">View on DVIDS</button>
                </a>
            </div>
        </div>
    </div>

    <script>
        const allItems = {items_json};
        const byCountry = {by_country_json};
        const byType = {by_type_json};
        const byBranch = {by_branch_json};
        const byCommand = {by_command_json};
        const deploymentCount = {deployment_count};

        // Region mapping
        const regionMap = {json.dumps(REGION_MAP)};

        // Command full names
        const commandNames = {{
            'INDOPACOM': 'U.S. Indo-Pacific Command',
            'CENTCOM': 'U.S. Central Command',
            'SOUTHCOM': 'U.S. Southern Command',
            'EUCOM': 'U.S. European Command'
        }};

        let currentFilters = {{
            type: 'all',
            branch: 'all',
            country: 'all',
            command: 'all',
            deployment: 'all',
            search: ''
        }};

        let currentTimeRange = 'daily';  // 'daily' (24h) or 'weekly' (7 days)
        const HOURS_IN_DAY = 24;
        const HOURS_IN_WEEK = 24 * 7;

        // Initialize filters
        function initFilters() {{
            // Type filters
            const typeContainer = document.getElementById('typeFilters');
            typeContainer.innerHTML = '<button class="filter-btn active" data-type="all" onclick="setTypeFilter(\\'all\\')">All Types <span class="filter-count">{digest.total_count}</span></button>';
            Object.entries(byType).sort((a, b) => b[1] - a[1]).forEach(([type, count]) => {{
                typeContainer.innerHTML += `<button class="filter-btn" data-type="${{type}}" onclick="setTypeFilter('${{type}}')">${{type.charAt(0).toUpperCase() + type.slice(1)}} <span class="filter-count">${{count}}</span></button>`;
            }});

            // Deployment filters
            const deployContainer = document.getElementById('deploymentFilters');
            deployContainer.innerHTML = '<button class="filter-btn active" data-deployment="all" onclick="setDeploymentFilter(\\'all\\')">All Content <span class="filter-count">{digest.total_count}</span></button>';
            if (deploymentCount > 0) {{
                deployContainer.innerHTML += `<button class="filter-btn" data-deployment="only" onclick="setDeploymentFilter('only')" style="background: rgba(255, 107, 53, 0.1); border-color: #ff6b35; color: #ff6b35;">DEPLOYMENTS ONLY <span class="filter-count">${{deploymentCount}}</span></button>`;
            }}

            // Command filters
            const commandContainer = document.getElementById('commandFilters');
            const cmdTotal = Object.values(byCommand).reduce((a, b) => a + b, 0);
            commandContainer.innerHTML = '<button class="filter-btn active" data-command="all" onclick="setCommandFilter(\\'all\\')">All Commands <span class="filter-count">' + cmdTotal + '</span></button>';
            ['INDOPACOM', 'CENTCOM', 'SOUTHCOM', 'EUCOM'].forEach(cmd => {{
                const count = byCommand[cmd] || 0;
                if (count > 0) {{
                    commandContainer.innerHTML += `<button class="filter-btn" data-command="${{cmd}}" onclick="setCommandFilter('${{cmd}}')">${{cmd}} <span class="filter-count">${{count}}</span></button>`;
                }}
            }});

            // Branch filters
            const branchContainer = document.getElementById('branchFilters');
            branchContainer.innerHTML = '<button class="filter-btn active" data-branch="all" onclick="setBranchFilter(\\'all\\')">All Branches <span class="filter-count">{digest.total_count}</span></button>';
            Object.entries(byBranch).sort((a, b) => b[1] - a[1]).forEach(([branch, count]) => {{
                branchContainer.innerHTML += `<button class="filter-btn" data-branch="${{branch}}" onclick="setBranchFilter('${{branch}}')">${{branch}} <span class="filter-count">${{count}}</span></button>`;
            }});

            // Country filters
            const countryContainer = document.getElementById('countryFilters');
            countryContainer.innerHTML = '<button class="filter-btn active" data-country="all" onclick="setCountryFilter(\\'all\\')">All Countries <span class="filter-count">{digest.total_count}</span></button>';
            Object.entries(byCountry).sort((a, b) => b[1] - a[1]).forEach(([country, count]) => {{
                countryContainer.innerHTML += `<button class="filter-btn" data-country="${{country}}" onclick="setCountryFilter('${{country}}')">${{country}} <span class="filter-count">${{count}}</span></button>`;
            }});
        }}

        function setTypeFilter(type) {{
            currentFilters.type = type;
            document.querySelectorAll('#typeFilters .filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.type === type));
            renderItems();
        }}

        function setCommandFilter(command) {{
            currentFilters.command = command;
            document.querySelectorAll('#commandFilters .filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.command === command));
            renderItems();
        }}

        function setBranchFilter(branch) {{
            currentFilters.branch = branch;
            document.querySelectorAll('#branchFilters .filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.branch === branch));
            renderItems();
        }}

        function setCountryFilter(country) {{
            currentFilters.country = country;
            document.querySelectorAll('#countryFilters .filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.country === country));
            renderItems();
        }}

        function setDeploymentFilter(deployment) {{
            currentFilters.deployment = deployment;
            document.querySelectorAll('#deploymentFilters .filter-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.deployment === deployment));
            renderItems();
        }}

        function filterItems() {{
            currentFilters.search = document.getElementById('searchInput').value.toLowerCase();
            renderItems();
        }}

        function setTimeRange(range) {{
            currentTimeRange = range;

            // Update toggle buttons
            document.getElementById('dailyBtn').classList.toggle('active', range === 'daily');
            document.getElementById('weeklyBtn').classList.toggle('active', range === 'weekly');

            // Update header text
            if (range === 'daily') {{
                document.getElementById('digestTitle').textContent = 'DVIDS DAILY DIGEST';
                document.getElementById('digestSubtitle').textContent = 'U.S. Navy & Marine Corps News | Last 24 Hours';
            }} else {{
                document.getElementById('digestTitle').textContent = 'DVIDS WEEKLY DIGEST';
                document.getElementById('digestSubtitle').textContent = 'U.S. Navy & Marine Corps News | {date_range}';
            }}

            // Update stats and re-render
            updateStats();
            renderItems();
        }}

        function updateStats() {{
            const maxHours = currentTimeRange === 'daily' ? HOURS_IN_DAY : HOURS_IN_WEEK;
            const timeFilteredItems = allItems.filter(item => item.hours_old <= maxHours);

            const total = timeFilteredItems.length;
            const newsCount = timeFilteredItems.filter(i => i.type === 'news').length;
            const imageCount = timeFilteredItems.filter(i => i.type === 'image').length;
            const videoCount = timeFilteredItems.filter(i => i.type === 'video').length;

            document.getElementById('statTotal').textContent = total;
            document.getElementById('statNews').textContent = newsCount;
            document.getElementById('statImages').textContent = imageCount;
            document.getElementById('statVideos').textContent = videoCount;
        }}

        function getFilteredItems() {{
            const maxHours = currentTimeRange === 'daily' ? HOURS_IN_DAY : HOURS_IN_WEEK;
            return allItems.filter(item => {{
                // Time range filter
                if (item.hours_old > maxHours) return false;
                if (currentFilters.type !== 'all' && item.type !== currentFilters.type) return false;
                if (currentFilters.branch !== 'all' && item.branch !== currentFilters.branch) return false;
                if (currentFilters.country !== 'all' && item.country !== currentFilters.country) return false;
                if (currentFilters.command !== 'all' && (!item.commands || !item.commands.includes(currentFilters.command))) return false;
                if (currentFilters.deployment === 'only' && !item.is_deployment) return false;
                if (currentFilters.search && !item.title.toLowerCase().includes(currentFilters.search) && !item.unit_name.toLowerCase().includes(currentFilters.search)) return false;
                return true;
            }});
        }}

        function renderItems() {{
            const filtered = getFilteredItems();
            const container = document.getElementById('contentContainer');
            document.getElementById('resultsCount').textContent = `Showing ${{filtered.length}} items`;

            if (filtered.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128269;</div>
                        <div class="empty-state-title">No items found</div>
                        <div class="empty-state-text">Try adjusting your filters or search terms</div>
                    </div>
                `;
                return;
            }}

            let html = '';

            // SECTION 0: Deployments (highlighted at top)
            const deploymentItems = filtered.filter(item => item.is_deployment);
            if (deploymentItems.length > 0) {{
                html += '<div class="section-group"><div class="section-title" style="color: #ff6b35; border-bottom-color: #ff6b35;">DEPLOYMENTS</div>';
                html += `
                    <div class="location-group">
                        <div class="location-header" style="background: rgba(255, 107, 53, 0.08);">
                            <span class="region-badge" style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: #000;">DEPLOY</span>
                            <span class="location-name" style="color: #ff6b35;">Ships &amp; Units Deploying</span>
                            <span class="location-count">${{deploymentItems.length}} item${{deploymentItems.length > 1 ? 's' : ''}}</span>
                        </div>
                        <div class="items-list">
                `;

                deploymentItems.forEach(item => {{
                    html += `
                        <div class="item-row ${{item.type}}" onclick="showDetail('${{item.id}}')" style="border-left-color: #ff6b35;">
                            <div class="item-row-type">
                                <span class="item-type ${{item.type}}">${{item.type}}</span>
                                <span class="deployment-tag">DEPLOY</span>
                            </div>
                            <div class="item-row-main">
                                <div class="item-row-title">${{item.title}}</div>
                                <div class="item-row-unit">${{item.unit_name}}</div>
                            </div>
                            <div class="item-row-meta">
                                <div class="item-row-branch">${{item.branch}}</div>
                                <div class="item-row-date">${{item.date_published}}</div>
                            </div>
                        </div>
                    `;
                }});

                html += '</div></div></div>';
            }}

            // SECTION 1: Combatant Commands
            const commandOrder = ['INDOPACOM', 'CENTCOM', 'SOUTHCOM', 'EUCOM'];
            const commandItems = {{}};
            const itemsInCommands = new Set();

            commandOrder.forEach(cmd => {{
                commandItems[cmd] = filtered.filter(item => item.commands && item.commands.includes(cmd));
                commandItems[cmd].forEach(item => itemsInCommands.add(item.id));
            }});

            const hasCommandItems = commandOrder.some(cmd => commandItems[cmd].length > 0);

            if (hasCommandItems) {{
                html += '<div class="section-group"><div class="section-title command">COMBATANT COMMANDS</div>';

                commandOrder.forEach(cmd => {{
                    const items = commandItems[cmd];
                    if (items.length === 0) return;

                    const fullName = commandNames[cmd] || cmd;
                    html += `
                        <div class="location-group">
                            <div class="location-header" style="background: rgba(255, 107, 107, 0.05);">
                                <span class="region-badge" style="background: rgba(255, 107, 107, 0.2); color: #ff6b6b;">${{cmd}}</span>
                                <span class="location-name" style="color: #ff6b6b;">${{fullName}}</span>
                                <span class="location-count">${{items.length}} item${{items.length > 1 ? 's' : ''}}</span>
                            </div>
                            <div class="items-list">
                    `;

                    items.forEach(item => {{
                        const deployTag = item.is_deployment ? '<span class="deployment-tag">DEPLOY</span>' : '';
                        html += `
                            <div class="item-row ${{item.type}}" onclick="showDetail('${{item.id}}')"${{item.is_deployment ? ' style="border-left-color: #ff6b35;"' : ''}}>
                                <div class="item-row-type">
                                    <span class="item-type ${{item.type}}">${{item.type}}</span>
                                    ${{deployTag}}
                                </div>
                                <div class="item-row-main">
                                    <div class="item-row-title">${{item.title}}</div>
                                    <div class="item-row-unit">${{item.unit_name}}</div>
                                </div>
                                <div class="item-row-meta">
                                    <div class="item-row-branch">${{item.branch}}</div>
                                    <div class="item-row-date">${{item.date_published}}</div>
                                </div>
                            </div>
                        `;
                    }});

                    html += '</div></div>';
                }});

                html += '</div>';
            }}

            // SECTION 2: By Geography (all items, grouped by country)
            const grouped = {{}};
            filtered.forEach(item => {{
                if (!grouped[item.country]) grouped[item.country] = [];
                grouped[item.country].push(item);
            }});

            const sortedCountries = Object.keys(grouped).sort((a, b) => grouped[b].length - grouped[a].length);

            if (sortedCountries.length > 0) {{
                html += '<div class="section-group"><div class="section-title geography">BY GEOGRAPHY</div>';

                sortedCountries.forEach(country => {{
                    const items = grouped[country];
                    const region = regionMap[country] || 'Other';

                    html += `
                        <div class="location-group">
                            <div class="location-header">
                                <span class="region-badge">${{region}}</span>
                                <span class="location-name">${{country}}</span>
                                <span class="location-count">${{items.length}} item${{items.length > 1 ? 's' : ''}}</span>
                            </div>
                            <div class="items-list">
                    `;

                    items.forEach(item => {{
                        const deployTag = item.is_deployment ? '<span class="deployment-tag">DEPLOY</span>' : '';
                        html += `
                            <div class="item-row ${{item.type}}" onclick="showDetail('${{item.id}}')"${{item.is_deployment ? ' style="border-left-color: #ff6b35;"' : ''}}>
                                <div class="item-row-type">
                                    <span class="item-type ${{item.type}}">${{item.type}}</span>
                                    ${{deployTag}}
                                </div>
                                <div class="item-row-main">
                                    <div class="item-row-title">${{item.title}}</div>
                                    <div class="item-row-unit">${{item.unit_name}}</div>
                                </div>
                                <div class="item-row-meta">
                                    <div class="item-row-branch">${{item.branch}}</div>
                                    <div class="item-row-date">${{item.date_published}}</div>
                                </div>
                            </div>
                        `;
                    }});

                    html += '</div></div>';
                }});

                html += '</div>';
            }}

            container.innerHTML = html;
        }}

        function showDetail(itemId) {{
            const item = allItems.find(i => i.id === itemId);
            if (!item) return;

            document.getElementById('modalTitle').textContent = item.title;
            document.getElementById('modalLink').href = item.url;

            let bodyHtml = '';

            if (item.thumbnail_url) {{
                bodyHtml += `<img class="modal-image" src="${{item.thumbnail_url}}" alt="">`;
            }}

            const deployBadge = item.is_deployment ? '<span class="modal-tag" style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: #000; font-weight: 700;">DEPLOYMENT</span>' : '';
            bodyHtml += `
                <div class="modal-meta">
                    <span class="modal-tag type">${{item.type}}</span>
                    <span class="modal-tag branch">${{item.branch}}</span>
                    <span class="modal-tag location">${{item.location_display}}</span>
                    ${{deployBadge}}
                </div>
            `;

            if (item.description) {{
                bodyHtml += `<div class="modal-description">${{item.description}}</div>`;
            }}

            bodyHtml += `
                <div class="modal-info">
                    <div class="modal-info-item">
                        <div class="modal-info-label">Unit</div>
                        <div class="modal-info-value">${{item.unit_name}}</div>
                    </div>
                    <div class="modal-info-item">
                        <div class="modal-info-label">Published</div>
                        <div class="modal-info-value">${{item.date_published}}</div>
                    </div>
                    ${{item.credit ? `<div class="modal-info-item"><div class="modal-info-label">Credit</div><div class="modal-info-value">${{item.credit}}</div></div>` : ''}}
                    ${{item.duration ? `<div class="modal-info-item"><div class="modal-info-label">Duration</div><div class="modal-info-value">${{item.duration}}</div></div>` : ''}}
                </div>
            `;

            document.getElementById('modalBody').innerHTML = bodyHtml;
            document.getElementById('detailModal').classList.add('visible');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal(event) {{
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('detailModal').classList.remove('visible');
            document.body.style.overflow = '';
        }}

        document.addEventListener('keydown', e => {{
            if (e.key === 'Escape') closeModal();
        }});

        // Initialize
        initFilters();
        setTimeRange('daily');  // Start with daily view
    </script>
</body>
</html>'''

    return html


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point for the DVIDS scraper."""
    print("=" * 70)
    print("  DVIDS DIGEST - U.S. Navy News Aggregator")
    print("  Daily/Weekly Toggle | Created by @ianellisjones and IEJ Media")
    print("=" * 70)

    # Check API key
    if DVIDS_API_KEY == "YOUR_API_KEY_HERE":
        print("\n  ERROR: Please set your DVIDS API key!")
        print("  Get a free key at: https://api.dvidshub.net/docs")
        print("  Then update DVIDS_API_KEY in this script.\n")
        return 1

    # Fetch weekly content
    items = fetch_daily_content(lookback_days=LOOKBACK_DAYS)

    if not items:
        print("  WARNING: No items fetched. Check your API key and connection.")
        # Create empty digest for display
        items = []

    # Create digest
    digest = create_daily_digest(items)

    # Generate HTML
    html_content = generate_dvids_html(digest)
    output_file = Path("dvids.html")
    output_file.write_text(html_content, encoding='utf-8')
    print(f"\n>>> HTML saved: {output_file}")

    # Also save JSON data for potential future use
    json_data = {
        "date": digest.date,
        "timestamp": datetime.utcnow().isoformat(),
        "total_count": digest.total_count,
        "by_country": digest.by_country,
        "by_type": digest.by_type,
        "by_branch": digest.by_branch,
        "by_command": digest.by_command,
        "items": [asdict(item) for item in digest.items]
    }
    json_file = Path("dvids_data.json")
    json_file.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    print(f">>> JSON saved: {json_file}")

    print(f"\n  Summary:")
    print(f"    Total items: {digest.total_count}")
    print(f"    News: {digest.by_type.get('news', 0)}")
    print(f"    Images: {digest.by_type.get('image', 0)}")
    print(f"    Videos: {digest.by_type.get('video', 0)}")
    print(f"    Deployments: {digest.deployment_count}")
    print(f"\n  Combatant Commands:")
    for cmd in ['INDOPACOM', 'CENTCOM', 'SOUTHCOM', 'EUCOM']:
        count = digest.by_command.get(cmd, 0)
        if count > 0:
            print(f"    {cmd}: {count}")
    print(f"\n  Top Countries:")
    for country, count in sorted(digest.by_country.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {country}: {count}")

    print(f"\n{'='*70}\n")

    return 0


if __name__ == "__main__":
    exit(main())
