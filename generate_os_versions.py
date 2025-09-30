def get_apple_os_versions():
    response = requests.get(APPLE_RELEASES_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    os_versions = {
        'iPadOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''},
        'macOS': {'current': None, 'current_date': '', 'upcoming': None, 'upcoming_date': ''}
    }

    # Find all version titles
    headlines = soup.find_all('h3', class_='headline')

    # Find all dates – they follow the headlines in order
    date_tags = soup.find_all('p', class_='date')
    dates = [d.text.strip() for d in date_tags]

    found_versions = {'iPadOS': [], 'macOS': []}

    for idx, h3 in enumerate(headlines):
        title = h3.text.strip()
        date_text = dates[idx] if idx < len(dates) else ''

        for os_type in ['iPadOS', 'macOS']:
            if title.startswith(os_type):
                match = re.search(rf'{os_type} (\d+\.\d+(?:\.\d+)?)', title)
                if match:
                    ver = match.group(1)
                    is_beta = 'beta' in title.lower() or 'rc' in title.lower()

                    if ver.startswith('26'):
                        found_versions[os_type].append({
                            'version': ver,
                            'date': date_text,
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
