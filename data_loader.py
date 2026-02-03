import sqlite3
import requests

WORDS_URL = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears-medium.txt"
DB_FILE = "vocab.db"
WORD_LIMIT = 3000

def fetch_words(url):

    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        words = content.strip().split('\n')
        return words[:WORD_LIMIT]
    except requests.RequestException as e:
        print(f"Error fetching words: {e}")
        return []

def populate_database(words):
    
    if not words:
        print("No words to insert.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
       
        data_to_insert = [(word, 'new') for word in words]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO words (word, status) VALUES (?, ?)",
            data_to_insert
        )
        conn.commit()
        print(f"Successfully inserted {len(words)} words into {DB_FILE}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Fetching word list...")
    top_words = fetch_words(WORDS_URL)
    
    if top_words:
        print(f"Fetched {len(top_words)} words. Inserting into database...")
        populate_database(top_words)
