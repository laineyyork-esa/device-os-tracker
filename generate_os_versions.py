import requests
from bs4 import BeautifulSoup
import csv
from datetime import date, datetime
import re
import os

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
    
    # Try ISO format (e.g., "2025-10-06")
    try:
        d = datetime.strptime(raw_date, "%Y-%m-%d")
        return d.strftime("%-d %B %Y")
    except ValueError:
        pass

    # Try format like "October 6, 2025"
    try:
        d = datetime.strptime(raw_date, "%B %d, %Y")
        return d.strftime("%-d %B %Y")
    except ValueError:
        pass

    # If all else fails
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
