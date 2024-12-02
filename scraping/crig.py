import requests
from bs4 import BeautifulSoup
import json
import time
import re

def clean_html(text):
    """Remove HTML tags and clean up whitespace."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_research_profile_url(name):
    """Convert researcher name to research.ugent.be profile URL."""
    formatted_name = name.lower().replace(' ', '-')
    return f"https://research.ugent.be/web/person/{formatted_name}-0/en"

def get_projects_url(name):
    """Convert researcher name to research.ugent.be projects URL."""
    formatted_name = name.lower().replace(' ', '-')
    return f"https://research.ugent.be/web/person/{formatted_name}-0/projects/en"

def get_project_description(project_url):
    """Fetch and extract the description from a project's detail page."""
    try:
        # Convert relative URLs to absolute
        if project_url.startswith('../'):
            # Extract the relevant part of the path after 'result/project/'
            match = re.search(r'result/project/(.+?)$', project_url)
            if match:
                project_path = match.group(1)
                project_url = f'https://research.ugent.be/web/result/project/{project_path}'
        elif project_url.startswith('/'):
            project_url = 'https://research.ugent.be' + project_url
            
        print(f"Fetching description from: {project_url}")  # Debug print
        response = requests.get(project_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        description_div = soup.find('div', {'id': 'description_showmore'})
        if description_div:
            # Find the paragraph within the description div
            description_p = description_div.find('p')
            if description_p:
                return clean_html(description_p.get_text())
            # If no paragraph found, try getting all text content
            return clean_html(description_div.get_text())
        return None
    except Exception as e:
        print(f"Error fetching project description: {str(e)}")
        return None

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
            faculty_link = position_div.find('a', href=lambda x: '/ge/en' in str(x))
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
                            if 'Description' in content:
                                description = content.split('Description')[1].split('Classification')[0]
                                description = clean_html(description)
                                discipline['description'] = description
                        
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

    # Scrape projects from the projects page
    projects_url = url.replace('/en', '/projects/en')
    try:
        projects_response = requests.get(projects_url)
        projects_soup = BeautifulSoup(projects_response.text, 'html.parser')
        
        projects = {'promotor': [], 'copromotor': [], 'fellow': []}
        
        # Find project sections by role
        for section in projects_soup.find_all('div', class_='margin-bottom-gl'):
            header = section.find('div', class_='header-5')
            if header:
                role_text = header.text.strip().lower()
                role = None
                if 'promotor' in role_text and 'co' not in role_text:
                    role = 'promotor'
                elif 'copromotor' in role_text:
                    role = 'copromotor'
                elif 'fellow' in role_text:
                    role = 'fellow'
                
                if role:
                    # Find all project titles and links in this section
                    for project in section.find_all('div', class_='fiche'):
                        project_link = project.find('a')
                        if project_link:
                            title_div = project_link.find('div', class_='header-6')
                            if title_div:
                                project_url = project_link['href']
                                if project_url.startswith('/'):
                                    project_url = 'https://research.ugent.be' + project_url
                                project_info = {
                                    'title': title_div.text.strip(),
                                    'url': project_url,
                                    'description': get_project_description(project_url)
                                }
                                projects[role].append(project_info)
                                # Add a small delay to avoid overwhelming the server
                                time.sleep(0.5)
        
        if any(projects.values()):  # Only add if there are any projects
            details['projects'] = projects
            
    except Exception as e:
        print(f"Error fetching projects: {str(e)}")

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
    print(f"Fetching research profile from {research_url}")
    
    try:
        details = scrape_researcher_details(research_url)
        researcher.update(details)
    except Exception as e:
        print(f"Error fetching research profile: {str(e)}")

    # To avoid overwhelming the server
    time.sleep(1)
    break

# Save the JSON data to a file with proper formatting
with open('scraping/researchers_crig.json', 'w', encoding='utf-8') as f:
    json.dump(researchers, f, indent=2, ensure_ascii=False)

print("\nScraping completed. Data saved to researchers_crig.json")
