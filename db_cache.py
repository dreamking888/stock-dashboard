#!/usr/bin/env python3
"""
Simple Database for Stock Dashboard
Stores historical data in SQLite for faster loading
"""

import sqlite3
import json
import os
from datetime import datetime

DB_FILE = 'stock_data.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS quotes 
                 (ticker TEXT PRIMARY KEY, data TEXT, updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (ticker TEXT, period TEXT, interval TEXT, data TEXT, updated TEXT,
                  PRIMARY KEY (ticker, period, interval))''')
    c.execute('''CREATE TABLE IF NOT EXISTS cache_log 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, result TEXT, timestamp TEXT)''')
    
    conn.commit()
    conn.close()

def save_quote(ticker, data):
    """Save quote to cache"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO quotes (ticker, data, updated) VALUES (?, ?, ?)',
              (ticker, json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_quote(ticker, max_age_seconds=300):
    """Get cached quote if fresh enough"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT data, updated FROM quotes WHERE ticker = ?', (ticker,))
    row = c.fetchone()
    conn.close()
    
    if row:
        data = json.loads(row[0])
        updated = datetime.fromisoformat(row[1])
        age = (datetime.now() - updated).total_seconds()
        if age < max_age_seconds:
            return data
    return None

def save_history(ticker, period, interval, data):
    """Save history to cache"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO history (ticker, period, interval, data, updated) VALUES (?, ?, ?, ?, ?)',
              (ticker, period, interval, json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history(ticker, period, interval, max_age_seconds=3600):
    """Get cached history if fresh enough"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT data, updated FROM history WHERE ticker = ? AND period = ? AND interval = ?',
              (ticker, period, interval))
    row = c.fetchone()
    conn.close()
    
    if row:
        data = json.loads(row[0])
        updated = datetime.fromisoformat(row[1])
        age = (datetime.now() - updated).total_seconds()
        if age < max_age_seconds:
            return data
    return None

def log_cache(action, result):
    """Log cache activity"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO cache_log (action, result, timestamp) VALUES (?, ?, ?)',
              (action, result, datetime.now().isoformat()))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized:", DB_FILE)
