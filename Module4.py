import argparse
import os
from Module1 import load_config,save_config,scrape_home_page
from Module2 import find_top_stories_link
from Module3 import scrape_article_headlines
from PIL import Image
from io import BytesIO
import psycopg2
import json
import requests
import re
from datetime import datetime

parser = argparse.ArgumentParser(description="Google News Scraper")
parser.add_argument("--base_url", type=str, help="Base URL for Google News")
parser.add_argument("--heading_text", type=str, help="Heading text for 'Top Stories'")
args = parser.parse_args()

# Load configuration
config = load_config()
if args.base_url:
    config["base_url"] = args.base_url
if args.heading_text:
    config["top_stories_heading"] = args.heading_text
save_config(config)

# Scrape the home page
print(f"Scraping home page from: {config['base_url']}")
soup = scrape_home_page(config["base_url"])

if soup:
    # Find the 'Top Stories' link
    print(f"Finding '{config['top_stories_heading']}' section...")
    top_stories_url = find_top_stories_link(soup, config["top_stories_heading"], config["base_url"])

    if top_stories_url:
        print(f"'Top Stories' URL: {top_stories_url}")
        # Scrape article headlines from the 'Top Stories' page
        print("Scraping article headlines...")
        headlines = scrape_article_headlines(top_stories_url,config['base_url'])
    else:
        print("Could not find the 'Top Stories' link.")


# Connection to database
def db_credential():
    with open("db_config.json", "r") as f:
        DB_Data = json.load(f)
    return DB_Data

DB_CONFIG=db_credential()
#Create 'images' folder for saving image files
images_folder = "images"
os.makedirs(images_folder, exist_ok=True)

# Database schema
CREATE_IMAGES_TABLE = """
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    image_name VARCHAR(255) UNIQUE NOT NULL,
    image_url TEXT NOT NULL
);
"""

CREATE_HEADLINES_TABLE = """
CREATE TABLE IF NOT EXISTS headlines (
    id SERIAL PRIMARY KEY,
    scrape_timestamp TIMESTAMP NOT NULL,
    headline TEXT NOT NULL,
    article_url TEXT NOT NULL,
    publish_date DATE,
    image_name VARCHAR(255),
    FOREIGN KEY (image_name) REFERENCES images(image_name) ON DELETE CASCADE
);
"""

# Function to save images and insert data into the database
def save_to_database(headlines, db_config, image_folder):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('set client_encoding to UTF8;')
        # Create tables if they don't exist
        cursor.execute(CREATE_IMAGES_TABLE)
        cursor.execute(CREATE_HEADLINES_TABLE)

        for headline,article_url,publish_time, image_url in headlines:
            try:
                # Fetch the image
                response = requests.get(image_url)
                response.raise_for_status()
                cursor.execute('''SELECT image_name
                                    FROM images
                                    ORDER BY CAST(regexp_replace(image_name, '\D', '', 'g') AS INTEGER) DESC LIMIT 1;''')
                last_image = cursor.fetchone()

                if last_image:
                    # Extract the number from the last image name using regex
                    match = re.search(r"headline_image_(\d+)\.jpg", last_image[0])
                    if match:
                        last_number = int(match.group(1))
                    else:
                        raise ValueError("Invalid image name format in the database.")
                else:
                    # If no images exist, start numbering from 1
                    last_number = 0
            
                img = Image.open(BytesIO(response.content))
                image_name = f"headline_image_{last_number+1}.jpg"
                file_path = os.path.join(image_folder, image_name)

                # Save the image locally
                img.convert('RGB').save(file_path)

                # Save the image data to the 'images' table
                cursor.execute(
                    """
                    INSERT INTO images (image_name, image_url)
                    VALUES (%s, %s) ON CONFLICT (image_name) DO NOTHING
                    """,
                    (image_name, image_url),
                )
                # Insert headline and meta-information into the headlines table
                cursor.execute(
                    """
                    INSERT INTO headlines (scrape_timestamp, headline, article_url, publish_date, image_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),headline, article_url, publish_time, image_name),
                )

                # Commit the transaction
                conn.commit()
                print(f"Successfully saved: {headline} -> {image_name}")

            except Exception as e:
                print(f"Failed to process: {headline}. Error: {e}")
                conn.rollback()

    except Exception as e:
        print(f"Database connection or setup failed: {e}")
    finally:
        cursor.close()
        conn.close()


def save_to_existing_database(headline, image_url, article_url, article_date, db_config,image_folder):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_config)

        cursor = conn.cursor()
        cursor.execute('set client_encoding to UTF8;')
        cursor.execute(CREATE_IMAGES_TABLE)
        cursor.execute(CREATE_HEADLINES_TABLE)
        # Fetch the last image name from the 'images' table
        cursor.execute('''SELECT image_name
                            FROM images
                            ORDER BY CAST(regexp_replace(image_name, '\D', '', 'g') AS INTEGER) DESC LIMIT 1;''')
        last_image = cursor.fetchone()

        if last_image:
            # Extract the number from the last image name using regex
            match = re.search(r"headline_image_(\d+)\.jpg", last_image[0])
            if match:
                last_number = int(match.group(1))
            else:
                raise ValueError("Invalid image name format in the database.")
        else:
            # If no images exist, start numbering from 1
            last_number = 0

        # Generate the new image name
        image_name = f"headline_image_{last_number + 1}.jpg"
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        file_path = os.path.join(image_folder, image_name)

        # Save the image locally
        img.convert('RGB').save(file_path)
        # Insert into the 'images' table
        cursor.execute("""
            INSERT INTO images (image_name, image_url)
            VALUES (%s, %s)
            ON CONFLICT (image_name) DO NOTHING;
        """, (image_name, image_url))

        # Insert into the 'headlines' table
        cursor.execute("""
            INSERT INTO headlines (scrape_timestamp, headline, article_url, publish_date, image_name)
            VALUES (%s, %s, %s, %s, %s);
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), headline, article_url, article_date, image_name))

        # Commit the transaction
        conn.commit()
        print(f"Saved to database: {headline} with image name {image_name}")

    except Exception as e:
        print(f"Error saving to the database: {e}")

    finally:
        cursor.close()
        conn.close()

        
# Save to database
if __name__=='__main__':
    save_to_database(headlines, DB_CONFIG,images_folder)

