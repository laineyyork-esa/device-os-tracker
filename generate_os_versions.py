import requests
from bs4 import BeautifulSoup
import csv
from datetime import date

APPLE_REleases_URL = 'https://developer.apple.com/news/releases/'

def parse_apple_releases():
    """
    Scrape the Apple Developer Releases page to collect version announcements and dates,
    especially for iPadOS and macOS.
    Returns:
      apple_info: dict mapping version → { 'os_type': 'iPadOS'/'macOS', 'date': 'YYYY-MM-DD', 'is_beta': bool }
    """
    resp = requests.get(APPLE_REleases_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = soup.find_all('article')

    apple_info = {}  # e.g. apple_info['26.1'] = {os_type: 'iPadOS', date: '2025-09-22', is_beta: True}

    for art in articles:
        # Look for date / time tag
        time_el = art.find('time')
        art_date = None
        if time_el:
            art_date = time_el.get_text().strip()
            # Optionally convert to YYYY-MM-DD format if it's in “Month Day, Year”
            # (you can parse with datetime.strptime)
            try:
                dt = date.fromisoformat(art_date)
                # if art_date was already YYYY-MM-DD, this works; else exception
                art_date = dt.isoformat()
            except Exception:
                # fallback: parse “September 22, 2025” etc.
                try:
                    dt2 = date.strptime(art_date, "%B %d, %Y")
                    art_date = dt2.isoformat()
                except Exception:
                    # leave art_date as original string
                    pass

        heading = art.find('h2')
        if not heading:
            continue
        title = heading.get_text().strip()

        # We expect titles like "iPadOS 26.1 beta (…)" or "macOS 26.1 beta (…)". Or maybe “iPadOS 26.0.1 (…)”
        for os_type in ('iPadOS', 'macOS'):
            if title.startswith(os_type):
                parts = title.split()
                if len(parts) >= 2:
                    version = parts[1]
                    is_beta = 'beta' in title or 'RC' in title or 'beta' in title.lower()
                    # Only store if not stored or newer (you can refine logic)
                    apple_info[version] = {
                        'os_type': os_type,
                        'date': art_date,
                        'is_beta': is_beta,
                        'title': title
                    }
                break

    return apple_info

def pick_current_and_upcoming(apple_info):
    """
    From apple_info (dict), pick:
      - current version (latest non-beta version)
      - upcoming version (first beta after current)
    Return:
      { 'iPadOS': {current: ver, current_date: d, upcoming: ver2, upcoming_date: d2}, 
        'macOS': { … } }
    """
    result = {
        'iPadOS': {'current': None, 'current_date': None, 'upcoming': None, 'upcoming_date': None},
        'macOS': {'current': None, 'current_date': None, 'upcoming': None, 'upcoming_date': None}
    }

    # Sort versions (lexical may not perfectly reflect numeric order, but often works for simple cases)
    for version, info in apple_info.items():
        os_type = info['os_type']
        # If it's not beta / RC, consider as candidate for current
        if not info['is_beta']:
            # pick the highest (lexicographically) as current
            if (result[os_type]['current'] is None) or (version > result[os_type]['current']):
                result[os_type]['current'] = version
                result[os_type]['current_date'] = info['date']
        else:
            # it's a beta (or upcoming). Use the first or latest beta as upcoming
            if (result[os_type]['upcoming'] is None) or (version > result[os_type]['upcoming']):
                result[os_type]['upcoming'] = version
                result[os_type]['upcoming_date'] = info['date']

    return result

def get_chromeos_info():
    """
    Return a dict for ChromeOS with fields:
       current_version, current_date, upcoming_version, upcoming_date
    This may need to be manual / fallback if scraping is unreliable.
    """
    # As a stub / fallback, you could hardcode or fetch from a known API or page.
    # For example:
    return {
        'current_version': '138',        # e.g. ChromeOS 138 stable now publicly
        'current_date': '',              # (if known)
        'upcoming_version': '139',       # next
        'upcoming_date': ''              # (if known)
    }

def get_windows_info():
    """
    Return a dict for Windows with fields:
       current_version, current_date, upcoming_version, upcoming_date
    Similar to ChromeOS, may need manual fallback or scraping Microsoft release health / roadmap.
    """
    # stub / fallback:
    return {
        'current_version': 'Windows 11 23H2',
        'current_date': '',            # e.g. when 23H2 was released
        'upcoming_version': 'Windows 11 24H1',
        'upcoming_date': ''            # (if known)
    }

def build_rows(apple_data, chromeos_info, windows_info):
    """
    Build CSV rows for all device types.
    apple_data has keys iPadOS, macOS with version/date info.
    """
    rows = []

    # iPad
    ipad = apple_data.get('iPadOS', {})
    rows.append({
        'Device Type': 'iPad',
        'Current OS Version': f"iPadOS {ipad.get('current', '')}" if ipad.get('current') else '',
        'Current OS Release Date': ipad.get('current_date', ''),
        'Upcoming OS Version': f"iPadOS {ipad.get('upcoming', '')}" if ipad.get('upcoming') else '',
        'Upcoming Release Date': ipad.get('upcoming_date', ''),
        'Release Notes URL': APPLE_REleases_URL
    })

    # Mac
    mac = apple_data.get('macOS', {})
    rows.append({
        'Device Type': 'MacBook',
        'Current OS Version': f"macOS {mac.get('current', '')}" if mac.get('current') else '',
        'Current OS Release Date': mac.get('current_date', ''),
        'Upcoming OS Version': f"macOS {mac.get('upcoming', '')}" if mac.get('upcoming') else '',
        'Upcoming Release Date': mac.get('upcoming_date', ''),
        'Release Notes URL': APPLE_REleases_URL
    })

    # ChromeOS
    cr = chromeos_info
    rows.append({
        'Device Type': 'Chromebook',
        'Current OS Version': f"ChromeOS {cr.get('current_version', '')}",
        'Current OS Release Date': cr.get('current_date', ''),
        'Upcoming OS Version': f"ChromeOS {cr.get('upcoming_version', '')}",
        'Upcoming Release Date': cr.get('upcoming_date', ''),
        'Release Notes URL': 'https://chromeos.dev/en/releases'
    })

    # Windows
    w = windows_info
    rows.append({
        'Device Type': 'Windows',
        'Current OS Version': w.get('current_version', ''),
        'Current OS Release Date': w.get('current_date', ''),
        'Upcoming OS Version': w.get('upcoming_version', ''),
        'Upcoming Release Date': w.get('upcoming_date', ''),
        'Release Notes URL': 'https://learn.microsoft.com/en-us/windows/release-health/'
    })

    return rows

def write_csv(rows):
    fields = [
        'Device Type',
        'Current OS Version',
        'Current OS Release Date',
        'Upcoming OS Version',
        'Upcoming Release Date',
        'Release Notes URL'
    ]
    with open('os_versions.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main():
    apple_info = parse_apple_releases()
    apple_data = pick_current_and_upcoming(apple_info)

    chromeos_info = get_chromeos_info()
    windows_info = get_windows_info()

    rows = build_rows(apple_data, chromeos_info, windows_info)
    write_csv(rows)
    print(f"[{date.today()}] Wrote os_versions.csv with {len(rows)} rows.")

if __name__ == '__main__':
    main()
