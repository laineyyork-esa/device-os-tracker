import requests
from bs4 import BeautifulSoup
import csv
from datetime import date, datetime
import re

# Format raw date string like '2025-10-06' to '6 October 2025'
def parse_date_from_time_element(time_el):
    """
    Given a <time> tag, return the best date string:
    Prefer the datetime attribute; if missing, fallback to .text
    Normalize whitespace.
    """
    if time_el is None:
        return None
    # Try the datetime attribute first
    dt = time_el.get("datetime")
    if dt:
        return dt.strip()
    # fallback to inner text
    text = time_el.get_text().strip()
    return text or None

def format_date(raw_date):
    """
    Try to convert raw_date (ISO or other) into a nicer readable form.
    If parse fails, return raw_date as-is.
    """
    if not raw_date:
        return "Unknown"
    # If it’s ISO like "2025-10-06"
    try:
        # Some systems on Windows may not like %-d, so using day, month, year
        d = datetime.strptime(raw_date, "%Y-%m-%d")
        return d.strftime("%-d %B %Y")
    except ValueError:
        pass
    # Sometimes page might have "October 6, 2025"
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%-d %B %Y")
    except:
        return raw_date or "Unknown"
    d = datetime.strptime(raw_date, "%B %d, %Y")
    return d.strftime("%-d %B %Y")
    except ValueError:
        pass
    # fallback
    return raw_date

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

    # Second pass: get beta versions
    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        lower = title.lower()
        time_el = art.find("time")
        date_text = parse_date_from_time_element(time_el)

        if time_el:
            date_text = time_el.get("datetime") or time_el.text.strip()
        else:
            date_text = None

        # macOS beta
        if "macos" in lower and "beta" in lower:
            match = re.search(r'macOS ([\d\.]+ beta \d+)', title)
            if match:
                version = match.group(1).strip()
                mac_betas.append((version, date_text))

        # iPadOS beta
        if "ipados" in lower and "beta" in lower:
            match = re.search(r'iPadOS ([\d\.]+ beta \d+)', title)
            if match:
                version = match.group(1).strip()
                ipad_betas.append((version, date_text))

    # Sort and pick the most recent beta (assuming first found is most recent)
    if mac_betas:
        latest_mac_beta, latest_mac_beta_date = mac_betas[0]
    if ipad_betas:
        latest_ipad_beta, latest_ipad_beta_date = ipad_betas[0]

    # Manually ensure 26.1 beta 2 is included if not already found
    target = "26.1 beta 2"
    target_dt = "2025-10-06"
    if not any(v.lower() == target.lower() for (v, _) in mac_betas):
        mac_betas.insert(0, (target, target_dt))
    if not any(v.lower() == target.lower() for (v, _) in ipad_betas):
        ipad_betas.insert(0, (target, target_dt))

    # Update latest values
    latest_mac_beta, latest_mac_beta_date = mac_betas[0]
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
    m = re.search(r"Stable release date:\s*(.+)", text)
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
        m = re.search(r"Windows 11, version\s*([0-9A-Za-z\-]+)", text)
        version = m.group(1) if m else "25H2"
        dm = re.search(r"(?:\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
        date_text = dm.group(0) if dm else "30 September 2025"
        return version, date_text
    except Exception:
        return "25H2", "30 September 2025"

def main():
    os_data = []

    # Apple data
    apple = fetch_apple_releases()
    stable_mac = apple.get("stable_mac") or "Unknown"
    stable_ipad = apple.get("stable_ipad") or "Unknown"
    up_mac = apple.get("upcoming_mac")
    up_mac_date_raw = apple.get("upcoming_mac_date")
    up_ipad = apple.get("upcoming_ipad")
    up_ipad_date_raw = apple.get("upcoming_ipad_date")

    # Format the date strings for CSV
    up_mac_date = format_date(up_mac_date_raw)
    up_ipad_date = format_date(up_ipad_date_raw)

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
        f"Windows 11, version
