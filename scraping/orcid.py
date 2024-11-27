# List of URLs to scrape
import requests
from bs4 import BeautifulSoup
import re
from linkedin_api import Linkedin


urls = [
    "https://research.ugent.be/web/person/sven-degroeve-0/en",
    # Add more URLs as needed
]

def get_orcid_from_url(url):
    try:
        # Fetch the page content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the request failed

        # Parse the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the ORCID link using a regular expression
        orcid_link = soup.find('a', href=re.compile(r"https://orcid.org/\d{4}-\d{4}-\d{4}-\d{4}"))
        
        if orcid_link:
            return orcid_link.text.strip()
        else:
            return "ORCID not found"
    except requests.RequestException as e:
        return f"Error fetching URL: {e}"

# Authenticate using your LinkedIn credentials
linkedin = Linkedin('sven.degroeve@gmail.com', 'Nba2@6VQ&hEN')

# Iterate through each URL and print the ORCID number
for url in urls:
    print(f"URL: {url}")
    orcid = get_orcid_from_url(url)
    print(f"ORCID: https://orcid.org/{orcid}")
    
