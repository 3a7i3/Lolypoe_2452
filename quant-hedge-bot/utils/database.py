"""
Database - Stockage des trades et donnees
"""

import sqlite3
import pandas as pd
from datetime import datetime
from config import DATABASE_PATH, DATABASE_TYPE
from utils.logger import logger

class TradeDatabase:
    """Gere la base de donnees des trades."""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise les tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                signal TEXT,
                entry_price REAL,
                quantity REAL,
                exit_price REAL,
                exit_time TEXT,
                pnl REAL,
                pnl_percent REAL,
                reason TEXT
            )
        ''')
        
        # Table des positions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE,
                quantity REAL,
                entry_price REAL,
                current_price REAL,
                pnl REAL,
                pnl_percent REAL,
                open_time TEXT,
                stop_loss REAL,
                take_profit REAL
            )
        ''')
        
        # Table des performances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY,
                date TEXT,
                daily_return REAL,
                cumulative_return REAL,
                drawdown REAL,
                sharpe_ratio REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def log_trade(self, symbol, signal, entry_price, quantity, exit_price=None, exit_time=None, pnl=None, reason=""):
        """Loggue un trade."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        pnl_percent = ((exit_price - entry_price) / entry_price * 100) if exit_price else None
        
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, signal, entry_price, quantity, 
                               exit_price, exit_time, pnl, pnl_percent, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), symbol, signal, entry_price, quantity, 
              exit_price, exit_time, pnl, pnl_percent, reason))
        
        conn.commit()
        conn.close()
    
    def update_position(self, symbol, quantity, entry_price, current_price, stop_loss, take_profit):
        """Met a jour une position."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        pnl = (current_price - entry_price) * quantity
        pnl_percent = ((current_price - entry_price) / entry_price * 100)
        
        cursor.execute('''
            INSERT OR REPLACE INTO positions 
            (symbol, quantity, entry_price, current_price, pnl, pnl_percent, 
             open_time, stop_loss, take_profit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, quantity, entry_price, current_price, pnl, pnl_percent, 
              datetime.now(), stop_loss, take_profit))
        
        conn.commit()
        conn.close()
    
    def get_all_trades(self):
        """Recupere tous les trades."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
        return df
    
    def get_positions(self):
        """Recupere les positions actives."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM positions", conn)
        conn.close()
        return df
    
    def get_performance_stats(self):
        """Recupere les stats de performance."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM performance ORDER BY date DESC", conn)
        conn.close()
        return df

# Instance globale
db = TradeDatabase()
