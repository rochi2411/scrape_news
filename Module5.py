import psycopg2
from Module4 import *
from fuzzywuzzy import fuzz


# Function to check if a tuple <headline, image> is already in the database
def is_duplicate(headline, db_config):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Query to fetch existing headlines and image hashes
        cursor.execute("SELECT headline FROM headlines;")
        existing_headlines = cursor.fetchall()

        # Check headline similarity
        for existing_headline in existing_headlines:
            similarity = fuzz.ratio(headline, existing_headline)
            if similarity > 85:  # Threshold for fuzzy match
                return True

        return False

    except Exception as e:
        print(f"Error checking for duplicates: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# Test the function
if __name__ == '__main__':

    for headline,article_url,article_date,image_url in headlines:
        if is_duplicate(headline, DB_CONFIG):
            print("Duplicate entry found.")
        else:
            save_to_existing_database(headline, image_url, article_url, article_date, DB_CONFIG,images_folder)
