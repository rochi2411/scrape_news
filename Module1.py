import requests
from bs4 import BeautifulSoup
import json


# Load configuration
CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "base_url": "https://news.google.com/",
            "top_stories_heading": "Top stories",
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def scrape_home_page(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.RequestException as e:
        print(f"Error fetching the home page: {e}")
        return None

# Test    
if __name__=='__main__':
    file=load_config()
    web_content=scrape_home_page(file['base_url'])