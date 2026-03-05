#!/usr/bin/env python3
"""
OPERATION EPIC FURY — Live Operations Dashboard Scraper
Version: 1.0.0

Fetches filtered news via RSS and DoD content via DVIDS API,
then injects live data into epicfury.html for 3× daily scheduled updates.

Schedule: 06:00, 12:00, 00:00 ET (11:00, 17:00, 05:00 UTC)
Triggered by: GitHub Actions · update-epicfury.yml

Created by @ianellisjones and IEJ Media
"""

import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from xml.etree import ElementTree as ET

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

DVIDS_API_KEY  = os.environ.get('DVIDS_API_KEY', '')
DVIDS_API_BASE = 'https://api.dvidshub.net'
LOOKBACK_DAYS  = 3   # days of content to pull from DVIDS
MAX_DVIDS      = 40  # max DVIDS items to embed
MAX_NEWS       = 60  # max news articles to embed

USER_AGENT = 'EpicFury-Dashboard/1.0 (Python; +https://github.com/ianellisjones/usn)'

# ══════════════════════════════════════════════════════════════════════
# RSS FEED SOURCES
# ══════════════════════════════════════════════════════════════════════

RSS_FEEDS = [
    {'url': 'https://feeds.bbci.co.uk/news/world/rss.xml',                       'name': 'BBC'},
    {'url': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',             'name': 'NYT'},
    {'url': 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',                       'name': 'WSJ'},
    {'url': 'https://news.usni.org/feed',                                        'name': 'USNI'},
    {'url': 'https://www.thedrive.com/the-war-zone/rss',                         'name': 'TWZ'},
    {'url': 'https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml', 'name': 'DefNews'},
    {'url': 'https://breakingdefense.com/feed/',                                 'name': 'BreakDef'},
    {'url': 'https://www.militarytimes.com/arc/outboundfeeds/rss/',              'name': 'MilTimes'},
    {'url': 'https://taskandpurpose.com/feed/',                                  'name': 'T&P'},
    {'url': 'https://foreignpolicy.com/feed/',                                   'name': 'FP'},
    {'url': 'https://www.stripes.com/news/rss',                                  'name': 'S&S'},
    {'url': 'https://www.aljazeera.com/xml/rss/all.xml',                         'name': 'AJE'},
    {'url': 'https://feeds.reuters.com/reuters/worldNews',                       'name': 'Reuters'},
]

# ══════════════════════════════════════════════════════════════════════
# KEYWORD FILTERS
# ══════════════════════════════════════════════════════════════════════

NEWS_KEYWORDS = [
    # Operation names
    'epic fury', 'operation epic fury', 'roaring lion', 'operation roaring lion',
    # US Forces
    'centcom', 'central command', '5th fleet', 'fifth fleet', 'u.s. central command',
    'eucom', 'european command', '6th fleet', 'sixth fleet', 'u.s. european command',
    'carrier strike group', 'expeditionary strike group',
    # Key ships
    'uss abraham lincoln', 'uss gerald r. ford', 'uss ford',
    # Conflict parties
    'iran', 'iranian', 'tehran', 'irgc', 'islamic revolutionary guard',
    'israel', 'israeli', 'idf',
    # Geography
    'strait of hormuz', 'persian gulf', 'gulf of oman', 'arabian sea', 'red sea',
    # Regional actors
    'hezbollah', 'houthi', 'houthis', 'yemen',
    # Conflict terms
    'missile strike', 'air strike', 'ballistic missile', 'cruise missile',
    'air defense', 'nuclear', 'middle east', 'mideast',
]

# DVIDS-specific: US forces only (DVIDS is DoD official, no adversary content needed)
DVIDS_KEYWORDS = [
    'centcom', 'central command', 'u.s. central command',
    '5th fleet', 'fifth fleet', 'navcent',
    'eucom', 'european command', 'u.s. european command',
    '6th fleet', 'sixth fleet', 'naveur',
    'epic fury', 'operation epic fury',
    # All 29 ships by name
    'uss abraham lincoln', 'uss gerald r. ford',
    'uss mitscher', 'uss mcfaul', 'uss delbert d. black',
    'uss pinckney', 'uss spruance', 'uss michael murphy',
    'uss frank e. petersen', 'uss john finn',
    'uss tulsa', 'uss canberra', 'uss santa barbara',
    'uss mount whitney', 'uss mahan', 'uss bainbridge',
    'uss winston s. churchill', 'uss thomas hudner',
    'uss oscar austin', 'uss roosevelt', 'uss bulkeley',
    'uss paul ignatius', 'uss lewis b. puller',
    'uss georgia', 'usns carl brashear', 'usns henry j. kaiser',
    'usns catawba', 'usns william mclean', 'usns marie tharp',
]

# ══════════════════════════════════════════════════════════════════════
# RSS FETCHING
# ══════════════════════════════════════════════════════════════════════

def fetch_rss(feed: dict, timeout: int = 15) -> list:
    """Fetch and parse a single RSS feed. Returns list of article dicts."""
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/xml, text/xml'}
    try:
        r = requests.get(feed['url'], headers=headers, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        print(f"  [SKIP] {feed['name']}: {e}")
        return []

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print(f"  [PARSE ERR] {feed['name']}: {e}")
        return []

    ns = {'atom': 'http://www.w3.org/2005/Atom', 'content': 'http://purl.org/rss/1.0/modules/content/'}
    items = root.findall('.//item') or root.findall('.//atom:entry', ns)
    articles = []

    for item in items:
        def txt(tag, fallback=''):
            el = item.find(tag) or item.find(f'atom:{tag}', ns)
            return (el.text or '').strip() if el is not None else fallback

        title   = txt('title')
        link    = txt('link') or txt('guid')
        desc    = re.sub(r'<[^>]+>', '', txt('description') or txt('content:encoded', '') or txt('summary', ''))
        pubdate = txt('pubDate') or txt('published') or txt('updated') or ''

        if title:
            articles.append({
                'title':   title,
                'link':    link,
                'desc':    desc.strip()[:250],
                'pubDate': pubdate,
                'source':  feed['name'],
            })

    return articles


def passes_news_filter(article: dict) -> bool:
    """Return True if the article is relevant to the operation."""
    text = (article['title'] + ' ' + article['desc']).lower()
    return any(kw in text for kw in NEWS_KEYWORDS)


def fetch_all_news() -> list:
    """Fetch all RSS feeds, filter by keywords, deduplicate, sort."""
    print('\n── Fetching RSS feeds ──')
    raw = []
    for feed in RSS_FEEDS:
        print(f'  {feed["name"]} ...', end=' ', flush=True)
        articles = fetch_rss(feed)
        filtered = [a for a in articles if passes_news_filter(a)]
        print(f'{len(filtered)}/{len(articles)} matched')
        raw.extend(filtered)
        time.sleep(0.3)  # polite delay

    # Deduplicate by title similarity
    seen_titles = set()
    deduped = []
    for a in raw:
        key = re.sub(r'[^a-z0-9]', '', a['title'].lower())[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(a)

    # Sort: newest first
    def parse_date(a):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(a['pubDate'])
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    deduped.sort(key=parse_date, reverse=True)
    print(f'  Total: {len(deduped)} unique matched articles')
    return deduped[:MAX_NEWS]


# ══════════════════════════════════════════════════════════════════════
# DVIDS API
# ══════════════════════════════════════════════════════════════════════

def dvids_request(endpoint: str, params: dict, retries: int = 3) -> dict | None:
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
    params['api_key'] = DVIDS_API_KEY
    url = DVIDS_API_BASE + endpoint

    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 403:
                print(f'  [ERR] DVIDS: Invalid API key')
                return None
            elif r.status_code == 429:
                wait = 2 ** attempt
                print(f'  [RATE LIMIT] Waiting {wait}s...')
                time.sleep(wait)
            else:
                print(f'  [HTTP {r.status_code}]')
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def passes_dvids_filter(title: str, desc: str, unit: str) -> bool:
    text = (title + ' ' + desc + ' ' + unit).lower()
    return any(kw in text for kw in DVIDS_KEYWORDS)


def detect_theater(text: str) -> list:
    theaters = []
    t = text.upper()
    if any(k in t for k in ['CENTCOM', 'CENTRAL COMMAND', '5TH FLEET', 'FIFTH FLEET', 'NAVCENT']):
        theaters.append('CENTCOM')
    if any(k in t for k in ['EUCOM', 'EUROPEAN COMMAND', '6TH FLEET', 'SIXTH FLEET', 'NAVEUR']):
        theaters.append('EUCOM')
    return theaters or ['JOINT']


def fetch_dvids() -> list:
    if not DVIDS_API_KEY:
        print('\n── DVIDS: No API key set, skipping ──')
        return []

    print('\n── Fetching DVIDS content ──')
    from_dt = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime('%Y-%m-%dT%H:%M:%SZ')
    items = []

    for ctype in ['news', 'image', 'video']:
        for branch in ['Navy', 'Marines', 'Joint']:
            params = {
                'type': ctype,
                'branch': branch,
                'from_date': from_dt,
                'max_results': 50,
                'sort': 'date',
            }
            result = dvids_request('/search', params)
            if result and 'results' in result:
                for raw in result['results']:
                    title = raw.get('title', '')
                    desc  = re.sub(r'<[^>]+>', '', raw.get('description', '') or raw.get('short_description', ''))
                    unit  = raw.get('unit_name', '')

                    if not passes_dvids_filter(title, desc, unit):
                        continue

                    pub = raw.get('date_published', raw.get('date', ''))
                    try:
                        ts = datetime.fromisoformat(pub.replace('Z', '+00:00')).isoformat()
                    except Exception:
                        ts = ''

                    theater = detect_theater(title + ' ' + desc + ' ' + unit)
                    thumb = ''
                    if 'images' in raw and raw['images']:
                        thumb = raw['images'].get('thumbnail', {}).get('url', '')

                    items.append({
                        'id':               str(raw.get('id', '')),
                        'title':            title,
                        'desc':             desc[:300],
                        'type':             ctype,
                        'branch':           branch,
                        'unit_name':        unit,
                        'timestamp':        ts,
                        'url':              raw.get('url', ''),
                        'thumbnail_url':    thumb,
                        'commands':         theater,
                        'location_display': raw.get('location', {}).get('display', '') if isinstance(raw.get('location'), dict) else '',
                    })
            time.sleep(0.2)

    # Deduplicate by ID
    seen = set()
    deduped = []
    for item in items:
        if item['id'] not in seen:
            seen.add(item['id'])
            deduped.append(item)

    # Sort newest first
    deduped.sort(key=lambda x: x['timestamp'], reverse=True)
    print(f'  Total: {len(deduped)} relevant DVIDS items')
    return deduped[:MAX_DVIDS]


# ══════════════════════════════════════════════════════════════════════
# HTML INJECTION
# ══════════════════════════════════════════════════════════════════════

def inject_into_html(news: list, dvids: list, output_path: str = 'epicfury.html'):
    """Read epicfury.html and inject fresh data, then write back."""
    html_path = Path(output_path)
    if not html_path.exists():
        print(f'[ERR] {output_path} not found — run from repo root')
        return False

    html = html_path.read_text(encoding='utf-8')

    # Replace DVIDS_DATA placeholder
    dvids_json = json.dumps(dvids, ensure_ascii=False, separators=(',', ':'))
    html = re.sub(
        r'const DVIDS_DATA\s*=\s*\[.*?\];',
        f'const DVIDS_DATA = {dvids_json};',
        html,
        flags=re.DOTALL
    )

    # Inject pre-fetched news articles as a separate constant (CACHED_NEWS_DATA)
    news_json = json.dumps(news, ensure_ascii=False, separators=(',', ':'))
    # Update or insert CACHED_NEWS_DATA constant after DVIDS_DATA line
    if 'const CACHED_NEWS_DATA' in html:
        html = re.sub(
            r'const CACHED_NEWS_DATA\s*=\s*\[.*?\];',
            f'const CACHED_NEWS_DATA = {news_json};',
            html,
            flags=re.DOTALL
        )
    else:
        html = html.replace(
            'const DVIDS_DATA = ',
            f'const CACHED_NEWS_DATA = {news_json};\nconst DVIDS_DATA = ',
        )

    # Update last-built timestamp comment at top
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    if '<!-- LAST_BUILT:' in html:
        html = re.sub(r'<!-- LAST_BUILT:.*?-->', f'<!-- LAST_BUILT: {ts} -->', html)
    else:
        html = html.replace('<head>', f'<head>\n<!-- LAST_BUILT: {ts} -->', 1)

    html_path.write_text(html, encoding='utf-8')
    print(f'\n✓ epicfury.html updated ({ts})')
    return True


# ══════════════════════════════════════════════════════════════════════
# CACHED NEWS BOOTSTRAP (server-side pre-load)
# ══════════════════════════════════════════════════════════════════════

def patch_cached_news_init(html_path: str = 'epicfury.html'):
    """
    After injection, patch the init() function to also render cached server-side
    news articles so the page shows content immediately on first load.
    """
    path = Path(html_path)
    html = path.read_text(encoding='utf-8')

    # Insert cached news rendering into the init block
    # Find init function and add CACHED_NEWS_DATA rendering
    cached_render = """
  // Load server-side cached news first (instant display, no fetch needed)
  if (typeof CACHED_NEWS_DATA !== 'undefined' && CACHED_NEWS_DATA.length) {
    allArticles = CACHED_NEWS_DATA;
    renderNews(allArticles);
    // Populate source filter buttons from cached data
    const cachedSources = [...new Set(CACHED_NEWS_DATA.map(a => a.source))].sort();
    const row = document.getElementById('src-filters');
    row.innerHTML = '<button class=\"flt-btn active\" onclick=\"filterNews(\'all\',this)\">All</button>';
    cachedSources.forEach(s => {
      const b = document.createElement('button');
      b.className = 'flt-btn'; b.textContent = s;
      b.onclick = function() { filterNews(s, this); };
      row.appendChild(b);
    });
    document.getElementById('loading-news').style.display = 'none';
  }"""

    # Only patch if CACHED_NEWS_DATA is present and init doesn't already have the patch
    if 'CACHED_NEWS_DATA' in html and 'Load server-side cached news' not in html:
        html = html.replace(
            'initGlobe();\n  renderDVIDS();\n  renderOSINT();\n  refreshAll();',
            cached_render + '\n  initGlobe();\n  renderDVIDS();\n  renderOSINT();\n  refreshAll();'
        )
        path.write_text(html, encoding='utf-8')


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    print('=' * 60)
    print('OPERATION EPIC FURY — Dashboard Scraper')
    print(f'Run time: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}')
    print('=' * 60)

    news  = fetch_all_news()
    dvids = fetch_dvids()

    ok = inject_into_html(news, dvids)
    if ok:
        patch_cached_news_init()

    # Save a data snapshot for debugging
    snapshot = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'news_count':  len(news),
        'dvids_count': len(dvids),
        'news':  news[:5],   # preview only
        'dvids': dvids[:5],
    }
    Path('epicfury_data.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    print(f'✓ Snapshot saved: epicfury_data.json')
    print(f'\nDone — {len(news)} news articles, {len(dvids)} DVIDS items')


if __name__ == '__main__':
    main()
