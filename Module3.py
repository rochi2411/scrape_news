import requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
from Module2 import find_top_stories_link
from Module1 import load_config, scrape_home_page

def date_time_format(datetimeiso):
    d = datetime.fromisoformat(datetimeiso[:-1]).astimezone(timezone.utc)
    return d.strftime('%Y-%m-%d %H:%M:%S')

def scrape_article_headlines(top_stories_url,base_url):
    try:
        response = requests.get(top_stories_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find article headlines
        article_tags = soup.find_all('article')
        
        for i,article in enumerate(article_tags):
            if(i%4==0):
                headline_tag = article.find('a', class_='gPFEn')
                figure_tag =  headline_tag.find_previous_sibling('figure') or headline_tag.find_next_sibling('figure') or headline_tag.find_parent('figure')
                publish_time=date_time_format(article.find('time')['datetime'])
                image_link = None
                article_link=None
                if figure_tag:
                    img_tag = figure_tag.find('img')
                    if img_tag and 'src' in img_tag.attrs:
                        image_link = base_url + img_tag['src'][1:]
                
                if headline_tag:
                    article_link=base_url.rstrip('/')+headline_tag['href'][1:]

                # Yield headline text, link, and image link
                yield headline_tag.text.strip(), article_link, publish_time, image_link
        return None
    except requests.RequestException as e:
        print(f"Error fetching the 'Top Stories' page: {e}")
        return []
    except Exception as e:
        print(f"Error extracting article headlines: {e}")
        return []

# Test
if __name__=='__main__':
    file=load_config()
    web_content=scrape_home_page(file['base_url'])
    link=find_top_stories_link(web_content,file['top_stories_heading'],file['base_url'])
    news_article=scrape_article_headlines(link,file['base_url'])
