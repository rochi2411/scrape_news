import logging
import argparse
import os
import psycopg2
from Module1 import load_config, save_config, scrape_home_page
from Module2 import find_top_stories_link
from Module3 import scrape_article_headlines
from Module4 import save_to_database,save_to_existing_database,db_credential, CREATE_HEADLINES_TABLE, CREATE_IMAGES_TABLE
from Module5 import is_duplicate

# Setup logging
log_file = "scrape_news.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

images_folder = "images"

def main():
    logging.info("Starting Google News Scraper Orchestration")
    try:
        # Load configuration
        config = load_config()
        base_url = config.get("base_url", "https://news.google.com/")
        heading_text = config.get("top_stories_heading", "Top stories")

        parser = argparse.ArgumentParser(description="Google News Scraper")
        parser.add_argument("--base_url", type=str, help="Base URL for Google News")
        parser.add_argument("--heading_text", type=str, help="Heading text for 'Top Stories'")
        args = parser.parse_args()

        if args.base_url:
            config["base_url"] = args.base_url
        if args.heading_text:
            config["top_stories_heading"] = args.heading_text
        save_config(config)

        # Step 1: Scrape Google News Home Page
        logging.info(f"Scraping home page from: {base_url}")
        soup = scrape_home_page(base_url)
        if not soup:
            logging.error("Failed to scrape the home page. Exiting.")
            return

        # Step 2: Find ‘Top Stories’ Section
        logging.info(f"Finding '{heading_text}' section...")
        top_stories_url = find_top_stories_link(soup, heading_text, base_url)
        if not top_stories_url:
            logging.error("Could not find 'Top Stories' link. Exiting.")
            return
        logging.info(f"Found 'Top Stories' URL: {top_stories_url}")

        # Step 3: Scrape Articles from ‘Top Stories’
        logging.info("Scraping article headlines...")
        headlines = scrape_article_headlines(top_stories_url, base_url)
        if not headlines:
            logging.warning("No headlines found.")
            return

        if os.path.exists(images_folder):
            logging.info("Folder already exists")
        else:
            os.makedirs(images_folder, exist_ok=True)
            logging.info("Making a folder to store the images")
       

        # Step 4: Set up the database and tables
        logging.info("Connecting to the database...")
        conn = psycopg2.connect(**DB_CONFIG)

        cursor = conn.cursor()
        cursor.execute('set client_encoding to UTF8;')
        cursor.execute(CREATE_IMAGES_TABLE)
        cursor.execute(CREATE_HEADLINES_TABLE)
        cursor.execute(f"SELECT COUNT(*) FROM headlines;")
        count = cursor.fetchone()[0]
        #save_to_database(headlines,DB_CONFIG,images_folder)
        logging.info("Connection is complete...")
        cursor.close()
        conn.close()

        if(count==0):
            logging.info("Save to the database...")
            save_to_database(headlines,DB_CONFIG,images_folder)
        else:
            # Step 4: Check for Duplicates & Save to Database
            for headline, article_url, article_date, image_url in headlines:
                if is_duplicate(headline, DB_CONFIG):
                    logging.info(f"Skipping duplicate: {headline}")
                else:
                    if image_url:
                        logging.info(f"Saving new articles to database...")
                        save_to_existing_database(headline,image_url, article_url, article_date, DB_CONFIG,images_folder)
                    else:
                        logging.warning(f"Skipping article '{headline}' due to invalid image URL: {image_url}")

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        logging.info("Orchestration completed.\n")    

if __name__ == "__main__":
    DB_CONFIG=db_credential()
    main()


