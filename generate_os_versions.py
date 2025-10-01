# generate_os_versions.py

import requests
from bs4 import BeautifulSoup
import csv
from datetime import date

# Data structure
os_data = []

# Apple - iPadOS and macOS
APPLE_URL = 'https://developer.apple.com/news/releases/'
response = requests.get(APPLE_URL)
soup = BeautifulSoup(response.text, 'html.parser')

# Basic scraper - search for macOS and iPadOS versions
articles = soup.find_all('article')

ipad_version = None
mac_version = None

for article in articles:
    heading = article.find('h2')
    if heading:
        text = heading.text
        if 'iPadOS' in text and not ipad_version:
            ipad_version = text.split()[1]
        elif 'macOS' in text and not mac_version:
            mac_version = text.split()[1]
    if ipad_version and mac_version:
        break

# Simulated upcoming versions and release dates (update manually or improve scraper logic)
os_data.append(["iPad", f"iPadOS {ipad_version}", "iPadOS 27", "2025-11-15", APPLE_URL])
os_data.append(["MacBook", f"macOS {mac_version}", "macOS 27", "2025-10-12", APPLE_URL])

# Placeholder for Chromebook and Windows - manual/static for now
os_data.append(["Chromebook", "ChromeOS 116", "ChromeOS 117", "2025-10-10", "https://chromeos.dev/en/releases"])
os_data.append(["Windows", "Windows 11 23H2", "Windows 11 24H1", "2025-11-01", "https://learn.microsoft.com/en-us/windows/release-health/"])

# Write to CSV
with open('os_versions.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Device Type", "Current OS Version", "Upcoming OS Version", "Upcoming Release Date", "Release Notes URL"])
    writer.writerows(os_data)

print(f"[{date.today()}] OS version data written to os_versions.csv")
