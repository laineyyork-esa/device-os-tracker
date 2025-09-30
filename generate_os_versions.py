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
    articles = soup.find_all('article')

    os_versions = {
        'iPadOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''},
        'macOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''}
    }

    version_data = {'iPadOS': [], 'macOS': []}

    for article in articles:
        heading = article.find('h2')
        date_el = article.find('time')
        if not heading or not date_el:
            continue

        title = heading.get_text(strip=True)
        release_date = date_el.get_text(strip=True)

        for os_type in ['iPadOS', 'macOS']:
            if title.startswith(os_type):
                match = re.search(rf'{os_type} (\d+\.\d+(\.\d+)?)', title)
                if match:
                    ver = match.group(1)
                    # Only include versions starting with 26
                    if ver.startswith('26'):
                        is_beta = 'beta' in title.lower() or 'rc' in title.lower()
                        version_data[os_type].append({
                            'version': ver,
                            'date': release_date,
                            'is_beta': is_beta
                        })

    for os_type in ['iPadOS', 'macOS']:
        stable_versions = [v for v in version_data[os_type] if not v['is_beta']]
        beta_versions = [v for v in version_data[os_type] if v['is_beta']]

        if stable_versions:
            latest_stable = max(stable_versions, key=lambda x: version.parse(x['version']))
            os_versions[os_type]['current'] = latest_stable['version']
            os_versions[os_type]['current_date'] = latest_stable['date']

        if beta_versions:
            latest_beta = max(beta_versions, key=lambda x: version.parse(x['version']))
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
