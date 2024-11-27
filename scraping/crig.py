import requests
from bs4 import BeautifulSoup
import json
import time

# Load HTML from the URL
url = 'https://www.crig.ugent.be/en/all-crig-group-leaders-and-members'
response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, 'html.parser')

# Find all researcher profile links
researchers = []
for node in soup.find_all('div', class_='node-partner'):
    link = node.find('a', class_='field-group-link')
    if link:
        profile_url = link['href']
        if not profile_url.startswith('http'):
            profile_url = 'https://www.crig.ugent.be' + profile_url
        img_tag = node.find('img')
        if img_tag and 'alt' in img_tag.attrs:
            name = img_tag['alt']
            researchers.append({'name': name, 'profile_url': profile_url})

# Parse the additional researcher list from the specific div
additional_section = soup.find('div', class_='field--name-field-rich-text')
if additional_section:
    for li in additional_section.find_all('li'):
        link = li.find('a')
        if link:
            name = link.text.strip()
            profile_url = link['href']
            if not profile_url.startswith('http'):
                profile_url = 'https://www.crig.ugent.be' + profile_url
            researchers.append({'name': name, 'profile_url': profile_url})

# Extract detailed information from each researcher's profile page
for researcher in researchers:
    print(researcher['name'])
    profile_url = researcher['profile_url']
    profile_response = requests.get(profile_url)
    profile_html = profile_response.text
    profile_soup = BeautifulSoup(profile_html, 'html.parser')

    # Extract description from meta tag
    description_tag = profile_soup.find('meta', {'name': 'description'})
    if description_tag:
        researcher['description'] = description_tag['content']

    # Extract keywords from meta tag
    keywords_tag = profile_soup.find('meta', {'name': 'keywords'})
    if keywords_tag:
        researcher['keywords'] = keywords_tag['content'].split(', ')

    # Extract research focus if available
    research_focus_header = profile_soup.find('h2', string='Research focus')
    if research_focus_header:
        focus_text = research_focus_header.find_next('div', class_='group-right').get_text(strip=True)
        researcher['research_focus'] = focus_text

    # Extract contact information if available
    contact_header = profile_soup.find('h2', string='Contact & links')
    if contact_header:
        contact_info = contact_header.find_next('div', class_='group-right').get_text(separator=' ', strip=True)
        researcher['contact_info'] = contact_info

        # Extract links if available
        links = []
        for link in contact_header.find_next('div', class_='group-right').find_all('a'):
            link_url = link.get('href')
            link_text = link.get_text(strip=True)
            links.append({'text': link_text, 'url': link_url})
        researcher['links'] = links

    # To avoid overwhelming the server, add a delay between requests
    time.sleep(0.1)

# Convert the list of researchers to JSON
researchers_json = json.dumps(researchers, indent=4)

# Save the JSON data to a file
with open('researchers_crig.json', 'w') as f:
    f.write(researchers_json)

# Display the JSON data
print(researchers_json)
