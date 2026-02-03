import sqlite3
from sqlite3 import Error
import os

DB_FILE = "vocab.db"

def create_connection(db_file):
   
    conn = None
    try:
        conn = sqlite3.connect(db_file)
       
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables(conn):
   
    sql_create_words_table = """
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL,
        phonetic TEXT,
        word_type TEXT,
        definition_tr TEXT,
        definition_en TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_sentences_table = """
    CREATE TABLE IF NOT EXISTS sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        sentence_text TEXT NOT NULL,
        level TEXT,
        translation TEXT,
        FOREIGN KEY (word_id) REFERENCES words (id) ON DELETE CASCADE
    );
    """

    sql_create_user_stats_table = """
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_words_learned INTEGER DEFAULT 0,
        current_streak INTEGER DEFAULT 0,
        last_practice_date TEXT
    );
    """

    try:
        c = conn.cursor()
        c.execute(sql_create_words_table)
        c.execute(sql_create_sentences_table)
        c.execute(sql_create_user_stats_table)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
       
        raise e

def main():
    database = DB_FILE

    
    conn = create_connection(database)

    if conn is not None:
        try:
           
            create_tables(conn)
            print("Database initialized successfully")
        except Error as e:
             print("Failed to initialize database structure.")
        finally:
            conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
