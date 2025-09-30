# generate_os_versions.py

import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

def parse_apple_releases():
    url = 'https://developer.apple.com/news/releases/'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = soup.find_all('article')

    # containers for what we want
    current = {
        'iPadOS': None,
        'macOS': None
    }
    upcoming = {
        'iPadOS': None,
        'macOS': None
    }
    dates = {}  # version → announcement date

    for art in articles:
        # Parse the date of the article
        # The page often shows “September 22, 2025” above entries. We need to detect that.
        date_el = art.find('time')
        art_date = None
        if date_el:
            art_date = date_el.get_text().strip()
        # Or fallback: look for a heading with date above series of items (you may need to inspect DOM)

        heading = art.find('h2')
        if heading:
            title = heading.get_text().strip()
            # Examples: "iPadOS 26.1 beta (23B5044l)"
            if title.startswith('iPadOS'):
                version = title.split()[1]  # e.g. "26.1"
                # if we don't have an upcoming version yet, set it
                if upcoming['iPadOS'] is None and 'beta' in title:
                    upcoming['iPadOS'] = version
                    dates[version] = art_date
                # also track current if the version matches “26.x” and not beta
                # (You might want logic to pick the latest non-beta in the list.)
            if title.startswith('macOS'):
                version = title.split()[1]
                if upcoming['macOS'] is None and 'beta' in title:
                    upcoming['macOS'] = version
                    dates[version] = art_date

    return current, upcoming, dates

def get_public_current_versions():
    """
    This is more heuristic / manual. Scrape Apple’s public OS pages or map from known sources.
    Returns something like:
      {'iPadOS': '26.0.1', 'macOS': '26.0'}
    """
    # Example: check https://www.apple.com/au/os/ipados/
    ipad_url = 'https://www.apple.com/au/os/ipados/'
    resp = requests.get(ipad_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # this likely yields "iPadOS 26" (no decimal) — so you may need a fallback or manual override
    title = soup.find('h1') or soup.find('title')
    current_ipados = None
    if title:
        txt = title.get_text()
        # extract “26” or “iPadOS 26” from it
        if 'iPadOS' in txt:
            # simplistic extraction
            current_ipados = txt.strip().split()[-1]

    # For macOS, similarly:
    mac_url = 'https://www.apple.com/au/os/macos/'
    resp2 = requests.get(mac_url)
    soup2 = BeautifulSoup(resp2.text, 'html.parser')
    current_macos = None
    title2 = soup2.find('h1') or soup2.find('title')
    if title2:
        txt2 = title2.get_text()
        if 'macOS' in txt2:
            current_macos = txt2.strip().split()[-1]

    return {
        'iPadOS': current_ipados,
        'macOS': current_macos
    }

def get_public_release_date(version, os_type):
    """
    Given a version like "26" or "26.0.1" and os_type "iPadOS" or "macOS",
    try to approximate or lookup the public release date.
    For example, many news sources say iOS/iPadOS/macOS 26 → September 15, 2025.
    """
    # simple mapping / fallback
    if version.startswith('26'):
        # known date for OS 26 public release
        return '2025-09-15'
    # else: return None or an empty string
    return ''

def build_data_row(os_type, current_ver, upcoming_ver, dates, release_date):
    return {
        'Device Type': 'iPad' if os_type == 'iPadOS' else 'MacBook',
        'Current OS Version': f"{os_type} {current_ver}" if current_ver else '',
        'Current OS Release Date': release_date,
        'Upcoming OS Version': f"{os_type} {upcoming_ver}" if upcoming_ver else '',
        'Upcoming Announcement Date': dates.get(upcoming_ver, ''),
        'Release Notes URL': 'https://developer.apple.com/news/releases/'
    }

def main():
    current, upcoming, dates = parse_apple_releases()
    public_current = get_public_current_versions()

    # build rows for iPadOS and macOS
    rows = []
    for os_type in ['iPadOS', 'macOS']:
        cur = public_current.get(os_type)
        up = upcoming.get(os_type)
        rel_date = get_public_release_date(cur, os_type)
        rows.append(build_data_row(os_type, cur, up, dates, rel_date))

    # Also include other device types (Chromebook, Windows) using your previous logic
    # ...
    # e.g. rows.append(...) for Chromebook, Windows

    # Write to CSV
    with open('os_versions.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Device Type', 'Current OS Version', 'Current OS Release Date',
            'Upcoming OS Version', 'Upcoming Announcement Date', 'Release Notes URL'
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print("Generated os_versions.csv")

if __name__ == '__main__':
    main()
