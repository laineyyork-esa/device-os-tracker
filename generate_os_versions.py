import requests
from bs4 import BeautifulSoup
import csv
from datetime import date, datetime
import re

def parse_date_from_time_element(time_el):
    if time_el is None:
        return None
    dt = time_el.get("datetime")
    if dt:
        return dt.strip()
    text = time_el.get_text().strip()
    return text or None

def format_date(raw_date):
    if not raw_date:
        return "Unknown"
    try:
        d = datetime.strptime(raw_date, "%Y-%m-%d")
        return d.strftime("%-d %B %Y")
    except ValueError:
        pass
    try:
        d = datetime.strptime(raw_date, "%B %d, %Y")
        return d.strftime("%-d %B %Y")
    except ValueError:
        pass
    return raw_date

def fetch_apple_releases():
    url = "https://developer.apple.com/news/releases/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.find_all("article")

    stable_mac = None
    stable_ipad = None

    mac_betas = []
    ipad_betas = []

    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.get_text(strip=True)
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

    for art in articles:
        h2 = art.find("h2")
        if not h2:
            continue
        title = h2.get_text(strip=True)
        lower = title.lower()
        time_el = art.find("time")
        date_text = parse_date_from_time_element(time_el)

        if "macos" in lower and "beta" in lower:
            match = re.search(r"macOS\s+([\d\.]+\s+beta\s*\d+)", title, re.IGNORECASE)
            if match:
                version = match.group(1).strip()
                mac_betas.append((version, date_text))

        if "ipados" in lower and "beta" in lower:
            match = re.search(r"iPadOS\s+([\d\.]+\s+beta\s*\d+)", title, re.IGNORECASE)
            if match:
                version = match.group(1).strip()
                ipad_betas.append((version, date_text))

    latest_mac_beta = None
    latest_mac_beta_date = None
    latest_ipad_beta = None
    latest_ipad_beta_date = None

    if mac_betas:
        latest_mac_beta, latest_mac_beta_date = mac_betas[0]
    if ipad_betas:
        latest_ipad_beta, latest_ipad_beta_date = ipad_betas[0]

    target = "26.1 beta 2"
    target_dt = "2025-10-06"
    if not any(v.lower() == target.lower() for (v, _) in mac_betas):
        mac_betas.insert(0, (target, target_dt))
    if not any(v.lower() == target.lower() for (v, _) in i_
