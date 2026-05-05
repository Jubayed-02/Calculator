import sqlite3
from datetime import datetime
import json

class CalculatorDB:
    def __init__(self, db_path="calculator_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        """Create history and settings tables"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT DEFAULT 'standard'
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Default settings
        self.cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('voice_enabled', 'true'), ('theme', 'dark')
        """)
        
        self.conn.commit()
    
    def add_history(self, expression, result, category="standard"):
        """Save calculation to history"""
        self.cursor.execute(
            "INSERT INTO history (expression, result, category) VALUES (?, ?, ?)",
            (expression, str(result), category)
        )
        self.conn.commit()
        print(self.cursor.lastrowid)
        return self.cursor.lastrowid
    
    def get_history(self, limit=50):
        """Retrieve recent history"""
        self.cursor.execute(
            "SELECT expression, result, timestamp, category FROM history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()
    
    def clear_history(self):
        """Clear all history"""
        self.cursor.execute("DELETE FROM history")
        self.conn.commit()
    
    def search_history(self, query):
        """Search through history"""
        self.cursor.execute(
            "SELECT expression, result, timestamp FROM history WHERE expression LIKE ? OR result LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
        return self.cursor.fetchall()