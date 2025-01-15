import sqlite3
from typing import Optional, Dict, Any
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(current_dir, "..", "database", "mydatabase.db")
DATABASE_PATH = os.path.normpath(DATABASE_PATH)
print(DATABASE_PATH)

class AnalyzeRequestDAO:
    """AnalyzeRequestDAO is a class that provides methods to interact with the AnalyzeRequest data."""

    def __init__(self):
        # No need for a model_name since we are directly using SQLite
        pass

    def _create_connection(self) -> sqlite3.Connection:
        """Create and return a connection to the SQLite database."""
        conn = sqlite3.connect(DATABASE_PATH)
        return conn

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
        """Insert a new AnalyzeRequest or update an existing one."""
        conn = self._create_connection()
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO AnalyzeRequest (wallet_address, count, text, engagement)
                          VALUES (?, ?, ?, ?)''', 
                          (data['wallet_address'], data['count'], data['text'], data['engagement']))

        conn.commit()
        conn.close()

        return data  # Return the inserted data as confirmation

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
