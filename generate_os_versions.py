import requests
from bs4 import BeautifulSoup
import csv
from datetime import date

def fetch_upcoming_from_apple_developer():
    """
    Scrape developer.apple.com/news/releases to get:
    - stable macOS (non-beta) version — for “current” macOS
    - upcoming / beta macOS version and its date
    - upcoming / beta iPadOS version and its date
    """
    url = "https://developer.apple.com/news/releases/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = soup.find_all("article")

    stable_mac = None
    upcoming_mac = None
    upcoming_mac_date = None
    upcoming_ipad = None
    upcoming_ipad_date = None

    # First, find stable macOS (non‑beta) by looking for "macOS X.Y" without “beta”
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        # Skip any title with “beta”
        if "macOS" in title and "beta" not in title:
            # e.g. “macOS 15.6 (24G84)” → want “15.6”
            parts = title.split()
            # We expect something like ["macOS", "15.6", ...]
            if len(parts) >= 2:
                stable_mac = parts[1]
                break

    # Next, find the upcoming / beta versions
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        time_el = art.find("time")
        date_text = time_el.text.strip() if time_el else None

        if "macOS" in title and upcoming_mac is None:
            # e.g. “macOS 26.1 beta (25B5042k)”
            parts = title.split()
            # parts[1] should be something like "26.1"
            if len(parts) >= 2:
                upcoming_mac = parts[1]
                upcoming_mac_date = date_text

        if "iPadOS" in title and upcoming_ipad is None:
            parts = title.split()
            if len(parts) >= 2:
                upcoming_ipad = parts[1]
                upcoming_ipad_date = date_text

        if upcoming_mac and upcoming_ipad:
            break

    return {
        "stable_mac": stable_mac,
        "mac": (upcoming_mac, upcoming_mac_date),
        "ipad": (upcoming_ipad, upcoming_ipad_date),
    }

def fetch_current_mac_from_apple_site():
    """
    Optional fallback: fetch from Apple’s macOS page for “current version” name.
    This might not always have version info in HTML; depends on site layout.
    """
    url = "https://www.apple.com/au/os/macos/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Try to find something like “macOS [Name] [Version]”
    # This is speculative: inspect the page to see where version is rendered
    # E.g. some <span class="version">, or in a heading
    # For now, fallback to None
    return None

def fetch_current_ipad_from_apple_site():
    """
    Optional fallback: fetch from Apple’s iPadOS page for current version.
    """
    url = "https://www.apple.com/au/ipados/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    return None

def fetch_windows_current_version_and_date():
    """
    Scrape Microsoft’s Windows 11 release information page to identify the latest announced feature update (e.g. 25H2) and its date.
    """
    url = "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Look for a table row containing “25H2” (or “version 25H2”) in <tr>
    for tr in soup.find_all("tr"):
        row_text = tr.get_text(separator="|").strip()
        # Use case-insensitive search
        if "25H2" in row_text or "version 25H2" in row_text:
            # Example: “Version 25H2 | Released September 30, 2025 | …”
            parts = [p.strip() for p in row_text.split("|")]
            ver = None
            dt = None
            for p in parts:
                low = p.lower()
                if low.startswith("version"):
                    # p might be like “Version 25H2”
                    ver = p.replace("Version", "").strip()
                # Very simplistic date detection: look for month names
                if any(m in p for m in ["January","February","March","April","May","June","July","August","September","October","November","December"]):
                    dt = p
            if ver:
                return ver, dt

    # Fallback: try to find a heading with “Windows 11 version” text
    for h in soup.find_all(["h2","h3","h4"]):
        txt = h.text.strip()
        if "Windows 11" in txt and "version" in txt:
            # e.g. “Windows 11 version 25H2”
            # Extract “25H2”
            parts = txt.split()
            for part in parts:
                if part.upper().endswith("H2"):
                    return part, None

    return None, None


def main():
    os_data = []

    # Get Apple developer upcoming & stable info
    apple = fetch_upcoming_from_apple_developer()
    stable_mac = apple.get("stable_mac")
    mac_up, mac_up_date = apple.get("mac", (None, None))
    ipad_up, ipad_up_date = apple.get("ipad", (None, None))

    # For current mac, prefer stable_mac; fallback to site scrape
    current_mac = stable_mac or fetch_current_mac_from_apple_site()
    # Prepend “macOS ” to version
    if current_mac:
        current_mac_str = f"macOS {current_mac}"
    else:
        current_mac_str = None

    upcoming_mac_str = f"macOS {mac_up}" if mac_up else None

    # For iPad: since you said iPad works okay, use the “ipad_up” value and fallback
    current_ipad = fetch_current_ipad_from_apple_site()
    current_ipad_str = f"iPadOS {current_ipad}" if current_ipad else None
    # If fallback fails and your logic has a way to derive current iPad version, you can set it manually
    # For upcoming:
    upcoming_ipad_str = f"iPadOS {ipad_up}" if ipad_up else None

    # Windows
    win_ver, win_date = fetch_windows_current_version_and_date()
    windows_current_str = None
    if win_ver:
        windows_current_str = f"Windows 11 version {win_ver}"

    # Append to os_data
    os_data.append([
        "MacBook",
        current_mac_str,
        upcoming_mac_str,
        mac_up_date,
        "https://developer.apple.com/news/releases/"
    ])
    os_data.append([
        "iPad",
        current_ipad_str,
        upcoming_ipad_str,
        ipad_up_date,
        "https://developer.apple.com/news/releases/"
    ])
    os_data.append([
        "Windows",
        windows_current_str,
        None,
        win_date,
        "https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information"
    ])
    # You can still include Chromebook logic separately as before

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

    print(f"[{date.today()}] OS version data written to os_versions.csv")

if __name__ == "__main__":
    main()
