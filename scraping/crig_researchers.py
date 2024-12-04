import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

def clean_html(text):
    """Remove HTML tags and clean up whitespace."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_research_profile_url(name):
    """Convert researcher name to research.ugent.be profile URL."""
    formatted_name = name.lower().replace(' ', '-')
    return f"https://research.ugent.be/web/person/{formatted_name}-0/en"

def get_publications_url(name):
    """Convert researcher name to research.ugent.be publications URL."""
    formatted_name = name.lower().replace(' ', '-')
    return f"https://research.ugent.be/web/person/{formatted_name}-0/publications/en"

def extract_publication_info(pub_div, year):
    """Extract publication information from a publication div."""
    publication = {'year': year}
    
    # Extract title
    title_span = pub_div.find('span', {'data-type': 'title'})
    if not title_span:
        return None
    publication['title'] = title_span.text.strip()
    
    # Extract authors
    authors = []
    authors_div = pub_div.find('div', class_='italic-text')
    if authors_div:
        for person_span in authors_div.find_all('span', {'data-type': 'person'}):
            authors.append(person_span.text.strip())
    if authors:
        publication['authors'] = authors
    
    # Get publication type
    type_span = pub_div.find('span', {'data-type': 'type'})
    if type_span:
        publication['type'] = type_span.text.strip()
    
    # Get journal/publication venue
    ref_title_span = pub_div.find('span', {'data-type': 'ref-title'})
    if ref_title_span:
        publication['venue'] = ref_title_span.text.strip()
    
    return publication

def scrape_researcher_details(url):
    """Scrape details from a researcher's profile page."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    details = {}

    # Extract current positions
    positions_div = soup.find('div', {'id': 'id1a'})
    if positions_div:
        positions = []
        for position_div in positions_div.find_all('div', class_='detailblokje'):
            position = {}
            
            # Title
            title_span = position_div.find('span', class_='header-6 text-black')
            if title_span:
                position['title'] = title_span.text.strip()
            
            # Faculty
            faculty_link = position_div.find('a', href=lambda x: x and '/ge/en' in x)
            if faculty_link:
                position['faculty'] = faculty_link.text.strip()
            
            # Department
            dept_span = position_div.find('span', class_='header-7 text-black')
            if dept_span:
                position['department'] = dept_span.text.strip()
            
            if position:
                positions.append(position)
        
        if positions:
            details['current_positions'] = positions

    # Extract research disciplines
    disciplines_div = soup.find('div', {'id': 'id23'})
    if disciplines_div:
        disciplines = []
        
        # Find all discipline categories
        for category_div in disciplines_div.find_all('div', class_='header-6'):
            category = {
                'category': category_div.text.strip(),
                'disciplines': []
            }
            
            # Find the ul that follows this category
            next_ul = category_div.find_next_sibling('ul')
            if next_ul:
                for li in next_ul.find_all('li'):
                    normal_span = li.find('span', class_='normal')
                    if normal_span:
                        discipline = {
                            'name': normal_span.text.strip(),
                            'code': normal_span.get('data-code', '')
                        }
                        
                        # Get description from popover
                        info_icon = li.find('span', class_='fas fa-info-circle')
                        if info_icon and 'data-content' in info_icon.attrs:
                            content = info_icon['data-content']
                            try:
                                if 'Description' in content:
                                    desc_parts = content.split('Description')
                                    if len(desc_parts) > 1:
                                        description = desc_parts[1]
                                        if 'Classification' in description:
                                            description = description.split('Classification')[0]
                                        description = clean_html(description)
                                        discipline['description'] = description
                            except Exception:
                                pass  # Skip description if there's an error
                        
                        category['disciplines'].append(discipline)
            
            if category['disciplines']:
                disciplines.append(category)
        
        if disciplines:
            details['research_disciplines'] = disciplines

    # Extract expertise
    expertise_div = soup.find('div', {'id': 'id24'})
    if expertise_div:
        keywords_div = expertise_div.find('div', class_='keywords')
        if keywords_div:
            expertise = []
            for keyword in keywords_div.find_all('span', class_='keyword-label'):
                if keyword.text.strip():
                    expertise.append(keyword.text.strip())
            
            if expertise:
                details['expertise'] = expertise

    # Scrape publications from the publications page
    publications_url = url.replace('/en', '/publications/en')
    try:
        publications_response = requests.get(publications_url)
        publications_soup = BeautifulSoup(publications_response.text, 'html.parser')
        
        publications = []
        current_year = datetime.now().year
        cutoff_year = current_year - 7  # Last 7 years
        
        # Track processed publications to avoid duplicates
        processed_titles = set()
        
        # Find all year sections
        year_sections = publications_soup.find_all('div', class_='margin-bottom-gl')
        
        for section in year_sections:
            # Get year from header
            year_header = section.find('div', class_='header-5')
            if not year_header:
                continue
                
            try:
                year = int(year_header.find('span').text.strip())
                if year < cutoff_year:
                    continue
                
                # Find publications container
                pubs_container = section.find('div', style='margin-left: 4em;')
                if not pubs_container:
                    continue
                
                # Find all publication divs
                for pub_div in pubs_container.find_all('div', class_='bg-blue-hover'):
                    # Extract title
                    title_span = pub_div.find('span', {'data-type': 'title'})
                    if not title_span:
                        continue
                        
                    title = title_span.text.strip()
                    # Skip if we've already processed this publication
                    if title in processed_titles:
                        continue
                    processed_titles.add(title)
                    
                    publication = {
                        'title': title,
                        'year': year
                    }

                    # Extract authors
                    authors = []
                    authors_div = pub_div.find('div', class_='italic-text')
                    if authors_div:
                        for person_span in authors_div.find_all('span', {'data-type': 'person'}):
                            authors.append(person_span.text.strip())
                    if authors:
                        publication['authors'] = authors

                    # Get publication type
                    type_span = pub_div.find('span', {'data-type': 'type'})
                    if type_span:
                        publication['type'] = type_span.text.strip()

                    # Get journal/publication venue
                    ref_title_span = pub_div.find('span', {'data-type': 'ref-title'})
                    if ref_title_span:
                        publication['venue'] = ref_title_span.text.strip()

                    publications.append(publication)
                    
            except (ValueError, AttributeError):
                continue

        if publications:  # Only add if there are any publications
            details['publications'] = publications
            
    except Exception as e:
        print(f"Error fetching publications: {str(e)}")

    return details

# Load HTML from the CRIG URL
url = 'https://www.crig.ugent.be/en/all-crig-group-leaders-and-members'
print(f"Fetching CRIG members from {url}")

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

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
    print(f"\nProcessing {researcher['name']}...")
    
    # First get CRIG profile info
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

    # Now get research.ugent.be profile info
    research_url = get_research_profile_url(researcher['name'])
    
    try:
        details = scrape_researcher_details(research_url)
        researcher.update(details)
    except Exception as e:
        print(f"Error fetching research profile: {str(e)}")

    # To avoid overwhelming the server
    time.sleep(1)
    break

# Save the JSON data to a file with proper formatting
with open('researchers_crig.json', 'w', encoding='utf-8') as f:
    json.dump(researchers, f, indent=2, ensure_ascii=False)

print("\nScraping completed. Data saved to researchers_crig.json")
