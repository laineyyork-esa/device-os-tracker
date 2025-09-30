import requests
from bs4 import BeautifulSoup
import csv
import re
from datetime import date
from packaging import version

APPLE_RELEASES_URL = 'https://developer.apple.com/news/releases/'

def get_apple_os_versions():
    response = requests.get(APPLE_RELEASES_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    releases = soup.find_all('h3')  # OS version titles now live in <h3> tags
    dates = soup.find_all('time')

    os_versions = {
        'iPadOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''},
        'macOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''}
    }

    found_versions = {
        'iPadOS': [],
        'macOS': []
    }

    for h3, time_tag in zip(releases, dates):
        title = h3.text.strip()
        release_date = time_tag.text.strip()

        for os_type in ['iPadOS', 'macOS']:
            if title.startswith(os_type):
                # Extract version (e.g., 26.0.1 or 26.1 beta)
                version_match = re.search(rf'{os_type} (\d+\.\d+(?:\.\d+)?)(?: beta)?', title)
                if version_match:
                    ver = version_match.group(1)
                    is_beta = 'beta' in title.lower() or 'rc' in title.lower()

                    if ver.startswith('26'):
                        found_versions[os_type].append({
                            'version': ver,
                            'date': release_date,
                            'is_beta': is_beta
                        })

    for os_type in ['iPadOS', 'macOS']:
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

    return os_versions

def get_chromeos_info():
    # Placeholder values — you can replace with dynamic scraping later
    return {
        'current_version': 'ChromeOS 138',
        'current_date': '',
        'upcoming_version': 'ChromeOS 139',
        'upcoming_date': ''
    }

def get_windows_info():
    # Placeholder values — you can replace with dynamic scraping later
    return {
        'current_version': 'Windows 11 23H2',
        'current_date': '',
        'upcoming_version': 'Windows 11 24H1',
        'upcoming_date': ''
    }

def write_csv(os_data):
    with open('os_versions.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Device Type",
            "Current OS Version",
            "Current OS Release Date",
            "Upcoming OS Version",
            "Upcoming Release Date",
            "Release Notes URL"
        ])
        writer.writerows(os_data)

def main():
    today = date.today()
    os_data = []

    # Apple data
    apple_versions = get_apple_os_versions()

    os_data.append([
        "iPad",
        f"iPadOS {apple_versions['iPadOS']['current']}",
        apple_versions['iPadOS']['current_date'],
        f"iPadOS {apple_versions['iPadOS']['upcoming']}",
        apple_versions['iPadOS']['upcoming_date'],
        APPLE_RELEASES_URL
    ])

    os_data.append([
        "MacBook",
        f"macOS {apple_versions['macOS']['current']}",
        apple_versions['macOS']['current_date'],
        f"macOS {apple_versions['macOS']['upcoming']}",
        apple_versions['macOS']['upcoming_date'],
        APPLE_RELEASES_URL
    ])

    # ChromeOS data
    chromeos = get_chromeos_info()
    os_data.append([
        "Chromebook",
        chromeos['current_version'],
        chromeos['current_date'],
        chromeos['upcoming_version'],
        chromeos['upcoming_date'],
        "https://chromeos.dev/en/releases"
    ])

    # Windows data
    windows = get_windows_info()
    os_data.append([
        "Windows",
        windows['current_version'],
        windows['current_date'],
        windows['upcoming_version'],
        windows['upcoming_date'],
        "https://learn.microsoft.com/en-us/windows/release-health/"
    ])

    write_csv(os_data)
    print(f"[{today}] os_versions.csv updated with {len(os_data)} rows.")

if __name__ == '__main__':
    main()
