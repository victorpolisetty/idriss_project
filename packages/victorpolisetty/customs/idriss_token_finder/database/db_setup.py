import sqlite3
from sqlite3 import Connection

# Path to your SQLite database file
DATABASE_PATH = "mydatabase.db"

def create_connection() -> Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_tables():
    """Create the required tables in the database."""
    conn = create_connection()
    cursor = conn.cursor()

    # Create AnalyzeRequest table
    cursor.execute('''CREATE TABLE IF NOT EXISTS AnalyzeRequest (
                        wallet_address TEXT PRIMARY KEY,
                        count INTEGER,
                        text TEXT,
                        engagement TEXT,
                        prompt TEXT)''')

    conn.commit()
    conn.close()

# Create tables when the script runs
create_tables()
