import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import date
from packaging import version

APPLE_RELEASES_URL = 'https://developer.apple.com/news/releases/'

def get_apple_os_versions():
    print("Fetching Apple releases page...")
    response = requests.get(APPLE_RELEASES_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Debug: print out some of the HTML around headlines/dates
    h3s = soup.find_all('h3', class_='headline')
    dates = soup.find_all('p', class_='date')
    print("Sample headlines:", [h.text.strip() for h in h3s[:5]])
    print("Sample dates:", [d.text.strip() for d in dates[:5]])

    os_versions = {
        'iPadOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''},
        'macOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''}
    }

    found_versions = {'iPadOS': [], 'macOS': []}

    for idx, h3 in enumerate(h3s):
        title = h3.text.strip()
        date_text = dates[idx].text.strip() if idx < len(dates) else ''
        # Debug
        print(f"Considering title: '{title}' with date '{date_text}'")

        for os_type in ('iPadOS', 'macOS'):
            if title.startswith(os_type):
                m = re.search(rf'{os_type} (\d+\.\d+(?:\.\d+)?)', title)
                if m:
                    ver = m.group(1)
                    is_beta = 'beta' in title.lower() or 'rc' in title.lower()
                    if ver.startswith('26'):
                        found_versions[os_type].append({
                            'version': ver,
                            'date': date_text,
                            'is_beta': is_beta
                        })

    print("Found versions dict:", found_versions)

    for os_type in ('iPadOS', 'macOS'):
        stable = [v for v in found_versions[os_type] if not v['is_beta']]
        beta = [v for v in found_versions[os_type] if v['is_beta']]

        if stable:
            latest_stable = max(stable, key=lambda x: version.parse(x['version']))
            os_versions[os_type]['current'] = latest_stable['version']
            os_versions[os_type]['current_date'] = latest_stable['date']
        if beta:
            latest_beta = max(beta, key=lambda x: version.parse(x['version']))
            os_versions[os_type]['upcoming'] = latest_beta['version']
            os_versions[os_type]['upcoming_date'] = latest_beta['date']

    print("Final os_versions:", os_versions)
    return os_versions

def get_chromeos_info():
    return {
        'current_version': 'ChromeOS 138',
        'current_date': '',
        'upcoming_version': 'ChromeOS 139',
        'upcoming_date': ''
    }

def get_windows_info():
    return {
        'current_version': 'Windows 11 23H2',
        'current_date': '',
        'upcoming_version': 'Windows 11 24H1',
        'upcoming_date': ''
    }

def build_rows(apple_versions, chromeos_info, windows_info):
    rows = []
    rows.append([
        "iPad",
        f"iPadOS {apple_versions['iPadOS']['current']}",
        apple_versions['iPadOS']['current_date'],
        f"iPadOS {apple_versions['iPadOS']['upcoming']}",
        apple_versions['iPadOS']['upcoming_date'],
        APPLE_RELEASES_URL
    ])
    rows.append([
        "MacBook",
        f"macOS {apple_versions['macOS']['current']}",
        apple_versions['macOS']['current_date'],
        f"macOS {apple_versions['macOS']['upcoming']}",
        apple_versions['macOS']['upcoming_date'],
        APPLE_RELEASES_URL
    ])
    rows.append([
        "Chromebook",
        chromeos_info['current_version'],
        chromeos_info['current_date'],
        chromeos_info['upcoming_version'],
        chromeos_info['upcoming_date'],
        "https://chromeos.dev/en/releases"
    ])
    rows.append([
        "Windows",
        windows_info['current_version'],
        windows_info['current_date'],
        windows_info['upcoming_version'],
        windows_info['upcoming_date'],
        "https://learn.microsoft.com/en-us/windows/release-health/"
    ])
    return rows

def write_csv(rows):
    with open('os_versions.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([
            "Device Type",
            "Current OS Version",
            "Current OS Release Date",
            "Upcoming OS Version",
            "Upcoming Release Date",
            "Release Notes URL"
        ])
        w.writerows(rows)

def main():
    print("Running script...")
    apple_versions = get_apple_os_versions()
    chromeos_info = get_chromeos_info()
    windows_info = get_windows_info()

    rows = build_rows(apple_versions, chromeos_info, windows_info)
    print("Rows to write:", rows)

    write_csv(rows)
    print("Wrote os_versions.csv")

if __name__ == '__main__':
    main()
