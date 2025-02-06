import sqlite3
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
# Define the base project directory (static)
BASE_DIR = Path("~/idriss_project")

# Resolve the database path relative to the base directory
DATABASE_PATH = BASE_DIR / "packages" / "victorpolisetty" / "customs" / "idriss_token_finder" / "database" / "mydatabase.db"

# Ensure the database directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

print(f"Resolved database path: {DATABASE_PATH}")

class AnalyzeRequestDAO:
    """AnalyzeRequestDAO is a class that provides methods to interact with the AnalyzeRequest data."""

    def __init__(self):
        # Ensure the database connection is available
        self._ensure_table_exists()

    def _create_connection(self) -> sqlite3.Connection:
        """Create and return a connection to the SQLite dataase."""
        return sqlite3.connect(DATABASE_PATH)
    

    def _ensure_table_exists(self):
        """Ensure the AnalyzeRequest table exists in the database."""
        conn = self._create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AnalyzeRequest (
                wallet_address TEXT PRIMARY KEY,
                count INTEGER,
                text TEXT,
                engagement TEXT,
                prompt TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("Table 'AnalyzeRequest' ensured in the database.")  # Debugging: Log table creation

    def get_by_wallet_address(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Retrieve an AnalyzeRequest by wallet address."""
        conn = self._create_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM AnalyzeRequest WHERE wallet_address = ?', (wallet_address,))
        row = cursor.fetchone()

        conn.close()

        if row:
            # Convert the row into a dictionary
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

        return None

    def insert(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a new AnalyzeRequest or update an existing one.

        Args:
            data (Dict[str, Any]): The data to insert, containing keys:
                - wallet_address (str): The unique wallet address (primary key).
                - count (int): Count of recasts, replies, etc.
                - text (str): Query text.
                - engagement (str): Type of engagement (e.g., "recasts", "replies").

        Returns:
            Optional[Dict[str, Any]]: The inserted data as confirmation.
        """
        # Create a connection to the database
        conn = self._create_connection()
        cursor = conn.cursor()

        try:
            # Log the incoming data for debugging
            print(f"Inserting data into AnalyzeRequest: {data}")

            # Execute the SQL insert statement
            cursor.execute('''INSERT INTO AnalyzeRequest (wallet_address, count, text, engagement)
                              VALUES (?, ?, ?, ?)''', 
                           (data['wallet_address'], data['count'], data['text'], data['engagement']))
            
            # Commit the transaction
            conn.commit()

            # Log success message
            print(f"Data successfully inserted into AnalyzeRequest: {data}")
        except sqlite3.IntegrityError as e:
            # Handle unique constraint violations or other database errors
            print(f"Failed to insert data into AnalyzeRequest: {data}, Error: {e}")
            return None
        except Exception as e:
            # Catch any other unexpected exceptions
            print(f"An error occurred during insert: {e}")
            return None
        finally:
            # Close the database connection
            conn.close()
            print("Database connection closed after insert.")

        # Return the inserted data as confirmation
        return data

    def update(self, wallet_address: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update an AnalyzeRequest by its wallet_address."""
        conn = self._create_connection()
        cursor = conn.cursor()

        # Create a dynamic SQL query for updating fields
        set_clause = ', '.join([f"{key} = ?" for key in kwargs])
        values = list(kwargs.values()) + [wallet_address]

        cursor.execute(f'''UPDATE AnalyzeRequest SET {set_clause} WHERE wallet_address = ?''', values)
        conn.commit()

        cursor.execute('SELECT * FROM AnalyzeRequest WHERE wallet_address = ?', (wallet_address,))
        row = cursor.fetchone()

        conn.close()

        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

        return None

    def delete(self, wallet_address: str) -> bool:
        """Delete an AnalyzeRequest by wallet_address."""
        conn = self._create_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM AnalyzeRequest WHERE wallet_address = ?', (wallet_address,))
        conn.commit()

        # Check if the deletion was successful
        cursor.execute('SELECT * FROM AnalyzeRequest WHERE wallet_address = ?', (wallet_address,))
        row = cursor.fetchone()

        conn.close()

        return row is None  # Returns True if the record was successfully deleted

    def get_all_requests(self) -> list[Dict[str, Any]]:
        """Get all AnalyzeRequests."""
        conn = self._create_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM AnalyzeRequest')
        rows = cursor.fetchall()

        conn.close()

        # Convert rows into a list of dictionaries
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
