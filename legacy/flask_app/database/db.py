import sqlite3
import os

DB_PATH = 'data.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            field TEXT NOT NULL,
            email TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            total_hours REAL,
            location TEXT,
            FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            assigned_to INTEGER,
            status TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (assigned_to) REFERENCES farmers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_type TEXT NOT NULL,
            confidence REAL,
            timestamp TEXT NOT NULL,
            field TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_log_id INTEGER,
            alert_type TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (animal_log_id) REFERENCES animal_logs (id)
        )
    ''')
    
    # Simple migration logic for existing DBs
    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE attendance ADD COLUMN location TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()

def execute_query(query, args=(), commit=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    if commit:
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
    else:
        results = cursor.fetchall()
        conn.close()
        return results

def execute_update(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()
