import sys
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_projects(name, json_data):
    # Convert the name to lowercase and replace spaces with hyphens for the URL format
    formatted_name = name.lower().replace(" ", "-")
    url = f"https://research.ugent.be/web/person/{formatted_name}-0/projects/en"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all project entries
    projects = soup.find_all('div', class_='fiche')

    if not projects:
        print("No projects found.")
        return

    # Create a list to hold project information
    project_list = []

    # Iterate over each project and extract the title, URL, "As" information, description, and keywords
    for project in projects:
        # Find the link tag within the project
        link = project.find('a', href=True)
        if link:
            title = project.find('div', class_='margin-bottom-ti').get('title')
            href = link['href']
            full_url = urljoin(url, href)
            as_info = project.find_previous('div', class_='header-5').text.strip() if project.find_previous('div', class_='header-5') else "N/A"
            
            # Fetch the project page to get the description and keywords
            try:
                project_response = requests.get(full_url)
                project_response.raise_for_status()
                project_soup = BeautifulSoup(project_response.content, 'html.parser')
                description = project_soup.find('div', id='description_showmore').text.strip() if project_soup.find('div', id='description_showmore') else "No description available"
                
                # Extract keywords and format them on one line separated by commas
                keywords_div = project_soup.find('div', class_='keywords')
                keywords = ", ".join([kw.text.strip() for kw in keywords_div.find_all('span')]) if keywords_div else "No keywords available"
            except requests.exceptions.RequestException as e:
                description = f"Error fetching project description: {e}"
                keywords = "Error fetching keywords"

            # Add the project information to the list
            project_list.append({
                "project_Title": title,
                "project_URL": full_url,
                "project_As": as_info,
                "project_Description": description,
                "project_Keywords": keywords
            })

    # Add the projects to the JSON data
    json_data["projects"] = project_list


def scrape_all_projects_in_json(json_path):
    # Load the JSON file
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    # Iterate over each person in the JSON and scrape their projects
    for person in data:
        name = person.get("name")
        if name:
            scrape_projects(name, person)

    # Save the updated JSON file
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    json_path = sys.argv[1]
    scrape_all_projects_in_json(json_path)
