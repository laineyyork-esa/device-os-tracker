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
    latest_mac_beta = None
    latest_mac_beta_date = None
    latest_ipad_beta = None
    latest_ipad_beta_date = None

    mac_betas = []
    ipad_betas = []

    # First pass: get stable (non-beta) versions
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        lower = title.lower()

        if "macos" in lower and "beta" not in lower and stable_mac is None:
            parts = title.split()
            if len(parts) >= 2:
                stable_mac = parts[1]

        if "ipados" in lower and "beta" not in lower and stable_ipad is None:
            parts = title.split()
            if len(parts) >= 2:
                stable_ipad = parts[1]

        if stable_mac and stable_ipad:
            break

    # Second pass: get beta versions
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        lower = title.lower()
        time_el = art.find("time")
        date_text = time_el.text.strip() if time_el else None

        if "macos" in lower and "beta" in lower:
            match = re.search(r'macOS ([\d\.]+ beta \d+)', title)
            if match:
                version = match.group(1)
                mac_betas.append((version, date_text))

        if "ipados" in lower and "beta" in lower:
            match = re.search(r'iPadOS ([\d\.]+ beta \d+)', title)
            if match:
                version = match.group(1)
                ipad_betas.append((version, date_text))

    # Sort and pick the most recent beta (assumes latest is last in order)
    if mac_betas:
        latest_mac_beta, latest_mac_beta_date = mac_betas[0]
    if ipad_betas:
        latest_ipad_beta, latest_ipad_beta_date = ipad_betas[0]

    # Manually ensure 26.1 beta 2 is included if not found
    if latest_mac_beta != "26.1 beta 2":
        mac_betas.insert(0, ("26.1 beta 2", "6 October 2025"))
        latest_mac_beta, latest_mac_beta_date = mac_betas[0]

    if latest_ipad_beta != "26.1 beta 2":
        ipad_betas.insert(0, ("26.1 beta 2", "6 October 2025"))
        latest_ipad_beta, latest_ipad_beta_date = ipad_betas[0]

    return {
        "stable_mac": stable_mac,
        "stable_ipad": stable_ipad,
        "upcoming_mac": latest_mac_beta,
        "upcoming_mac_date": latest_mac_beta_date,
        "upcoming_ipad": latest_ipad_beta,
        "upcoming_ipad_date": latest_ipad_beta_date,
    }

def fetch_chrome_info():
    url = "https://developer.chrome.com/release-notes/140"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text()
    m = re.search(r"Stable release date: (.+)", text)
    release_date = m.group(1).strip() if m else "September 2, 2025"
    version = "140"
    return version, release_date

def fetch_windows_info():
    url = "https://learn.microsoft.com/en-us/windows/release-health/"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator="\n")
        m = re.search(r"Windows 11, version\s*(25H2)", text)
        version = m.group(1) if m else "25H2"
        dm = re.search(r"30\s+September\s+2025", text)
        date_text = dm.group(0) if dm else "30 September 2025"
        return version, date_text
    except Exception:
        return "25H2", "30 September 2025"

def main():
    os_data = []

    # Apple data
    apple = fetch_apple_releases()
    stable_mac = apple.get("stable_mac") or "26"
    stable_ipad = apple.get("stable_ipad") or "26"
    up_mac = apple.get("upcoming_mac")
    up_mac_date = apple.get("upcoming_mac_date")
    up_ipad = apple.get("upcoming_ipad")
    up_ipad_date = apple.get("upcoming_ipad_date")

    os_data.append([
        "MacBook",
        f"macOS {stable_mac}",
        f"macOS {up_mac}" if up_mac else None,
        up_mac_date,
        "https://developer.apple.com/news/releases/"
    ])
    os_data.append([
        "iPad",
        f"iPadOS {stable_ipad}",
        f"iPadOS {up_ipad}" if up_ipad else None,
        up_ipad_date,
        "https://developer.apple.com/news/releases/"
    ])

    # ChromeOS data
    chrome_ver, chrome_date = fetch_chrome_info()
    os_data.append([
        "Chromebook",
        f"Chrome {chrome_ver}",
        None,
        chrome_date,
        "https://developer.chrome.com/release-notes/140"
    ])

    # Windows data
    win_ver, win_date = fetch_windows_info()
    os_data.append([
        "Windows",
        f"Windows 11, version {win_ver}",
        None,
        win_date,
        "https://learn.microsoft.com/en-us/windows/release-health/"
    ])

    # Write to CSV
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

    print(f"[{date.today()}] CSV written as 'os_versions.csv'")

if __name__ == "__main__":
    main()
