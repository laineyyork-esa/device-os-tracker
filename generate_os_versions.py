import requests
from bs4 import BeautifulSoup
import csv
from datetime import date, datetime
import re
import os

# ---------- Utility Functions ----------

def parse_date_from_time_element(time_el):
    """Try to extract a date from a <time> element."""
    if not time_el:
        return None
    dt = time_el.get("datetime")
    if dt:
        return dt.strip()
    return time_el.get_text(strip=True) or None

def format_date(raw_date):
    """Normalize date strings into readable '6 October 2025' format."""
    if not raw_date:
        return "Unknown"
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw_date, fmt).strftime("%-d %B %Y")
        except ValueError:
            continue
    return raw_date

# ---------- Scraping Functions ----------

def fetch_apple_releases():
    """Fetch current and upcoming macOS/iPadOS releases from Apple Developer."""
    url = "https://developer.apple.com/news/releases/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    articles = soup.find_all("section", {"class": "article-content-container"})

    stable_mac = None
    stable_ipad = None
    mac_betas, ipad_betas = [], []

    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.text.strip()
        link = h2.find("a")["href"] if h2.find("a") else url
        if link.startswith("/"):
            link = f"https://developer.apple.com{link}"

        date_el = art.find("p", {"class": "article-date"})
        date_text = date_el.text.strip() if date_el else None

        lower = title.lower()

        # Stable releases
        if "macos" in lower and "beta" not in lower and not stable_mac:
            parts = title.split()
            if len(parts) >= 2:
                stable_mac = {"version": parts[1], "link": link}

        if "ipados" in lower and "beta" not in lower and not stable_ipad:
            parts = title.split()
            if len(parts) >= 2:
                stable_ipad = {"version": parts[1], "link": link}

        # Beta releases
        if "macos" in lower and "beta" in lower:
            match = re.search(r'macOS ([\d\.]+ beta \d+)', title)
            if match:
                mac_betas.append({
                    "version": match.group(1),
                    "date": date_text,
                    "link": link
                })
        if "ipados" in lower and "beta" in lower:
            match = re.search(r'iPadOS ([\d\.]+ beta \d+)', title)
            if match:
                ipad_betas.append({
                    "version": match.group(1),
                    "date": date_text,
                    "link": link
                })

    latest_mac_beta = mac_betas[-1] if mac_betas else None
    latest_ipad_beta = ipad_betas[-1] if ipad_betas else None

    return {
        "stable_mac": stable_mac,
        "stable_ipad": stable_ipad,
        "upcoming_mac": latest_mac_beta,
        "upcoming_ipad": latest_ipad_beta
    }

def fetch_chrome_info():
    """
    Fetch current stable and beta Chrome OS release information from developer.chrome.com
    """
    stable_url = "https://developer.chrome.com/release-notes/"
    beta_url = "https://developer.chrome.com/blog/"

    # Fetch Stable Info
    resp = requests.get(stable_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the first "release notes" link (usually the latest stable)
    stable_link = None
    stable_ver = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"/release-notes/\d+", href):
            stable_link = "https://developer.chrome.com" + href
            match = re.search(r"(\d+)", href)
            if match:
                stable_ver = match.group(1)
            break

    # Default fallback values
    stable_ver = stable_ver or "Unknown"
    stable_date = "Unknown"

    # Fetch Beta Info
    resp_b = requests.get(beta_url)
    resp_b.raise_for_status()
    soup_b = BeautifulSoup(resp_b.text, "html.parser")
    beta_link = None
    beta_ver = None
    for a in soup_b.find_all("a", href=True):
        href = a["href"]
        if re.search(r"/blog/chrome-\d+-beta", href):
            beta_link = "https://developer.chrome.com" + href
            match = re.search(r"chrome-(\d+)-beta", href)
            if match:
                beta_ver = match.group(1)
            break

    # Get published date from that beta article
    beta_date = "Unknown"
    if beta_link:
        resp_beta = requests.get(beta_link)
        resp_beta.raise_for_status()
        soup_beta = BeautifulSoup(resp_beta.text, "html.parser")
        time_tag = soup_beta.find("time")
        if time_tag and time_tag.get("datetime"):
            beta_date = format_date(time_tag["datetime"])

    return {
        "stable_version": stable_ver,
        "stable_date": stable_date,
        "stable_link": stable_link or stable_url,
        "beta_version": beta_ver or "Unknown",
        "beta_date": beta_date,
        "beta_link": beta_link or beta_url,
    }

def fetch_windows_info():
    """Fetch Windows 11 version and date."""
    url = "https://learn.microsoft.com/en-us/windows/release-health/"
    resp = requests.get(url)
    resp.raise_for_status()
    text = resp.text
    m = re.search(r"Windows 11, version\s*([0-9A-Za-z\-]+)", text)
    version = m.group(1) if m else "Unknown"
    dm = re.search(r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
    date_text = dm.group(1) if dm else "Unknown"
    return {"version": version, "date": date_text, "link": url}

# ---------- Comparison + CSV ----------

def compare_with_previous_csv(new_rows, filename):
    """Compare new CSV rows with existing CSV; mark ⚠️ for changed fields."""
    if not os.path.exists(filename):
        return new_rows  # First run
    old_rows = []
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        old_rows = list(reader)
    highlighted = []
    for i, row in enumerate(new_rows):
        if i < len(old_rows):
            old = old_rows[i]
            new = [
                (f"{new_cell} ⚠️" if old[j] != new_cell else new_cell)
                for j, new_cell in enumerate(row)
            ]
            highlighted.append(new)
        else:
            highlighted.append([f"{c} ⚠️" for c in row])
    return highlighted

def main():
    os_data = []

    # Apple
    apple = fetch_apple_releases()
    mac_stable = apple["stable_mac"]
    mac_beta = apple["upcoming_mac"]
    ipad_stable = apple["stable_ipad"]
    ipad_beta = apple["upcoming_ipad"]

    os_data.append([
        "MacBook",
        f"macOS {mac_stable['version']}" if mac_stable else "Unknown",
        f"macOS {mac_beta['version']}" if mac_beta else None,
        format_date(mac_beta["date"]) if mac_beta else "Unknown",
        mac_beta["link"] if mac_beta else mac_stable["link"]
    ])
    os_data.append([
        "iPad",
        f"iPadOS {ipad_stable['version']}" if ipad_stable else "Unknown",
        f"iPadOS {ipad_beta['version']}" if ipad_beta else None,
        format_date(ipad_beta["date"]) if ipad_beta else "Unknown",
        ipad_beta["link"] if ipad_beta else ipad_stable["link"]
    ])

    # Chrome
    chrome = fetch_chrome_info()
    os_data.append([
        "Chromebook",
        f"Chrome {chrome['stable_version']}",
        f"Chrome {chrome['beta_version']} Beta",
        format_date(chrome["beta_date"]),
        chrome["beta_link"]
    ])

    # Windows
    win = fetch_windows_info()
    os_data.append([
        "Windows",
        f"Windows 11, version {win['version']}",
        None,
        format_date(win["date"]),
        win["link"]
    ])

    # Save clean CSV
    header = ["Device Type", "Current OS Version", "Upcoming OS Version",
              "Upcoming Release Date", "Release Notes URL"]

    with open('os_versions.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(os_data)

    # Highlighted version
    highlighted = compare_with_previous_csv(os_data, 'os_versions.csv')
    with open('highlighted_os_versions.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(highlighted)

    print(f"[{date.today()}] CSVs written and compared.")

if __name__ == "__main__":
    main()
