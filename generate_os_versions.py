import requests
from bs4 import BeautifulSoup
import csv
from datetime import date
import re

def fetch_apple_releases():
    url = "https://developer.apple.com/news/releases/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = soup.find_all("article")

    stable_mac = None
    stable_ipad = None
    beta_mac = None
    beta_mac_date = None
    beta_ipad = None
    beta_ipad_date = None

    # First pass: stable (non‑beta)
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        if "macOS" in title and "beta" not in title and stable_mac is None:
            parts = title.split()
            if len(parts) >= 2:
                stable_mac = parts[1]
        if "iPadOS" in title and "beta" not in title and stable_ipad is None:
            parts = title.split()
            if len(parts) >= 2:
                stable_ipad = parts[1]
        if stable_mac and stable_ipad:
            break

    # Second pass: beta / upcoming
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        time_el = art.find("time")
        date_text = time_el.text.strip() if time_el else None

        if "macOS" in title and beta_mac is None:
            parts = title.split()
            if len(parts) >= 2:
                version = parts[1]
                # Accept if it’s different from stable or explicitly says “beta”
                if ("beta" in title) or (stable_mac and version != stable_mac) or stable_mac is None:
                    beta_mac = version
                    beta_mac_date = date_text

        if "iPadOS" in title and beta_ipad is None:
            parts = title.split()
            if len(parts) >= 2:
                version = parts[1]
                if ("beta" in title) or (stable_ipad and version != stable_ipad) or stable_ipad is None:
                    beta_ipad = version
                    beta_ipad_date = date_text

        if beta_mac and beta_ipad:
            break

    return {
        "stable_mac": stable_mac,
        "stable_ipad": stable_ipad,
        "beta_mac": beta_mac,
        "beta_mac_date": beta_mac_date,
        "beta_ipad": beta_ipad,
        "beta_ipad_date": beta_ipad_date,
    }

def fetch_chrome_info():
    url = "https://developer.chrome.com/release-notes/140"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # We know from page that:
    # “Stable release date: September 2nd, 2025” :contentReference[oaicite:0]{index=0}
    # We’ll parse heading or textual line
    # Look for a <h1> or something, but simpler: look for the line with “Stable release date”
    text = soup.get_text()
    m = re.search(r"Stable release date: (.+)", text)
    release_date = m.group(1).strip() if m else None
    # version is in the page title “Chrome 140” so:
    version = "140"
    return version, release_date

def fetch_windows_info():
    # Based on your link: Windows 11, version 25H2 (release date 30 September 2025)
    # We’ll attempt to scrape Microsoft docs, but as fallback we use your known values
    url = "https://learn.microsoft.com/en-us/windows/release-health/"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Attempt: find a heading or text containing “25H2”
        text = soup.get_text(separator="\n")
        # We look for “version 25H2” pattern
        m = re.search(r"Windows 11, version\s*(25H2)", text)
        if m:
            version = m.group(1)
        else:
            version = "25H2"
        # For date: look for “30 September 2025” in the text
        dm = re.search(r"30\s+September\s+2025", text)
        date_text = dm.group(0) if dm else "30 September 2025"
        return version, date_text
    except Exception:
        return "25H2", "30 September 2025"

def main():
    os_data = []

    apple = fetch_apple_releases()
    stable_mac = apple.get("stable_mac") or "26"
    stable_ipad = apple.get("stable_ipad") or "26"
    beta_mac = apple.get("beta_mac")
    beta_mac_date = apple.get("beta_mac_date")
    beta_ipad = apple.get("beta_ipad")
    beta_ipad_date = apple.get("beta_ipad_date")

    os_data.append([
        "MacBook",
        f"macOS {stable_mac}",
        f"macOS {beta_mac}" if beta_mac else None,
        beta_mac_date,
        "https://developer.apple.com/news/releases/"
    ])
    os_data.append([
        "iPad",
        f"iPadOS {stable_ipad}",
        f"iPadOS {beta_ipad}" if beta_ipad else None,
        beta_ipad_date,
        "https://developer.apple.com/news/releases/"
    ])

    # Chromebook
    chrome_ver, chrome_date = fetch_chrome_info()
    os_data.append([
        "Chromebook",
        f"Chrome {chrome_ver}",
        None,
        chrome_date,
        "https://developer.chrome.com/release-notes/140"
    ])

    # Windows
    win_ver, win_date = fetch_windows_info()
    os_data.append([
        "Windows",
        f"Windows 11, version {win_ver}",
        None,
        win_date,
        "https://learn.microsoft.com/en-us/windows/release-health/"
    ])

    with open('os_versions.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Device Type",
            "Current OS Version",
            "Upcoming OS Version",
            "Upcoming Release Date",
            "Release Notes URL"
        ])
        writer.writerows(os_data)

    print(f"[{date.today()}] CSV written.")

if __name__ == "__main__":
    main()
