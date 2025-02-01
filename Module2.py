from Module1 import load_config,scrape_home_page

# Scrap to obtain the top stories link
def find_top_stories_link(soup, heading_text, base_url):
    try:
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if heading_text.lower() in heading.get_text(strip=True).lower():
                top_stories_anchor = heading.find_next('a', class_='aqvwYd', href=True)
                if top_stories_anchor:
                    top_stories_url = top_stories_anchor['href']
                    # Ensure the URL is absolute
                    if top_stories_url.startswith('./'):
                        top_stories_url = base_url.rstrip('/') + top_stories_url[1:]
                    return top_stories_url
        print(f"'{heading_text}' section not found.")
        return None
    except Exception as e:
        print(f"Error finding 'Top Stories' link: {e}")
        return None
    
# Test    
if __name__=='__main__':
    file=load_config()
    web_content=scrape_home_page(file['base_url'])
    link=find_top_stories_link(web_content,file['top_stories_heading'],file['base_url'])