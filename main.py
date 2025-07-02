import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from sqlite3 import Error
import calendar
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import tempfile
import os
import base64
from io import BytesIO
import hashlib
from PIL import Image
import time
import yfinance as yf
from forex_python.converter import CurrencyRates
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.seasonal import seasonal_decompose

# ========== Page Configuration ==========
st.set_page_config(
    page_title="💰 Advanced Finance Tracker Pro+", 
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="expanded"
)

# ========== Enhanced Custom CSS ==========
st.markdown("""
    <style>
        :root {
            --primary-color: #4f8bf9;
            --secondary-color: #6c757d;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .stHeader {
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .stDataFrame {
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.8rem;
            text-align: center;
        }
        
        .ag-theme-streamlit {
            --ag-grid-size: 5px;
            --ag-list-item-height: 30px;
        }
        
        .notes-cell {
            white-space: normal !important;
            line-height: 1.5 !important;
        }
        
        /* Custom tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Custom buttons */
        .stButton>button {
            border-radius: 8px;
            padding: 8px 16px;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Custom select boxes */
        .stSelectbox>div>div>select {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom number inputs */
        .stNumberInput>div>div>input {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom date inputs */
        .stDateInput>div>div>input {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom text inputs */
        .stTextInput>div>div>input {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom text areas */
        .stTextArea>div>div>textarea {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom checkboxes */
        .stCheckbox>label {
            margin-bottom: 0;
        }
        
        /* Custom radio buttons */
        .stRadio>div {
            gap: 15px;
        }
        
        /* Custom progress bars */
        .stProgress>div>div>div {
            background-color: var(--primary-color);
        }
        
        /* Custom success message */
        .stAlert.stAlert-success {
            border-left: 4px solid var(--success-color);
        }
        
        /* Custom error message */
        .stAlert.stAlert-error {
            border-left: 4px solid var(--danger-color);
        }
        
        /* Custom warning message */
        .stAlert.stAlert-warning {
            border-left: 4px solid var(--warning-color);
        }
        
        /* Custom info message */
        .stAlert.stAlert-info {
            border-left: 4px solid var(--info-color);
        }
        
        /* Custom tooltips */
        .stTooltip {
            border-radius: 8px;
            padding: 8px 12px;
        }
        
        /* Custom sidebar */
        .css-1d391kg {
            padding-top: 2rem;
        }
        
        .danger-zone {
            border: 2px solid var(--danger-color);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        /* Custom transaction cards */
        .transaction-card {
            border-left: 4px solid;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .income-card {
            border-color: #2ecc71;
            background-color: rgba(46, 204, 113, 0.1);
        }
        
        .expense-card {
            border-color: #e74c3c;
            background-color: rgba(231, 76, 60, 0.1);
        }
        
        /* Custom tabs content */
        .tab-content {
            padding: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# ========== Authentication Functions ==========
def hash_password(password):
    """Hash a password for storing."""
    salt = "finance_tracker_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def initialize_auth_db():
    """Initialize authentication database"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                cursor.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        preferences TEXT
                    )
                ''')
                conn.commit()
            else:
                cursor.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cursor.fetchall()]
                required_columns = ['id', 'username', 'password_hash', 'email', 'created_at', 'last_login', 'preferences']
                
                for col in required_columns:
                    if col not in columns:
                        if col == 'last_login':
                            cursor.execute('ALTER TABLE users ADD COLUMN last_login TIMESTAMP')
                        elif col == 'preferences':
                            cursor.execute('ALTER TABLE users ADD COLUMN preferences TEXT')
                        conn.commit()
        except Error as e:
            st.error(f"Failed to initialize auth database: {e}")
        finally:
            conn.close()

def create_user(username, password, email=None):
    """Create a new user"""
    conn = create_connection()
    if conn is not None:
        try:
            password_hash = hash_password(password)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', (username, password_hash, email))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Failed to create user: {e}")
            return False
        finally:
            conn.close()
    return False

def verify_user(username, password):
    """Verify user credentials"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, password_hash FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            if result:
                user_id, stored_hash = result
                if stored_hash == hash_password(password):
                    cursor.execute('''
                        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                    ''', (user_id,))
                    conn.commit()
                    return user_id
        except Error as e:
            st.error(f"Failed to verify user: {e}")
        finally:
            conn.close()
    return None

def get_user_preferences(user_id):
    """Get user preferences"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT preferences FROM users WHERE id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return eval(result[0])
        except Error as e:
            st.error(f"Failed to get user preferences: {e}")
        finally:
            conn.close()
    return {}

def update_user_preferences(user_id, preferences):
    """Update user preferences"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET preferences = ? WHERE id = ?
            ''', (str(preferences), user_id))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Failed to update user preferences: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Database Functions ==========
def create_connection():
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect('finance.db')
        return conn
    except Error as e:
        st.error(f"Database connection failed: {e}")
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL DEFAULT "Other",
                    type TEXT NOT NULL,
                    account TEXT NOT NULL DEFAULT "Cash",
                    recurring BOOLEAN DEFAULT 0,
                    recurring_frequency TEXT,
                    recurring_end_date DATE,
                    notes TEXT,
                    tags TEXT,
                    receipt BLOB,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    month_year TEXT NOT NULL,
                    user_id INTEGER,
                    notifications BOOLEAN DEFAULT 1,
                    UNIQUE(category, month_year, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL,
                    target_date DATE,
                    notes TEXT,
                    priority INTEGER DEFAULT 3,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    balance REAL NOT NULL,
                    currency TEXT DEFAULT 'IDR',
                    institution TEXT,
                    account_number TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investment_portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol TEXT,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    purchase_date DATE,
                    current_value REAL,
                    quantity REAL,
                    purchase_price REAL,
                    notes TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    user_id INTEGER,
                    UNIQUE(name, type, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL,
                    target_date DATE,
                    priority INTEGER DEFAULT 3,
                    notes TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    amount REAL,
                    category TEXT,
                    type TEXT,
                    account TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Enhanced default categories (limited to requested categories)
            default_categories = [
                # Income Categories (only Salary)
                ('Salary', 'Income'),
                
                # Expense Categories (only the 6 requested)
                ('Bills & Utilities', 'Expense'),
                ('Shopping', 'Expense'),
                ('Education', 'Expense'),
                ('Healthcare', 'Expense'),
                ('Entertainment', 'Expense'),
                ('Transportation', 'Expense')
            ]
            
            for category in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, type)
                    VALUES (?, ?)
                ''', category)
            
            cursor.execute("INSERT OR IGNORE INTO accounts (name, type, balance, currency) VALUES (?, ?, ?, ?)",
                         ("Cash", "Cash", 0, "IDR"))
            
            conn.commit()
        except Error as e:
            st.error(f"Failed to create tables: {e}")
        finally:
            conn.close()

def migrate_database():
    """Add missing columns to existing database"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            tables = {
                'transactions': ['user_id', 'category', 'account', 'recurring', 'notes', 'tags', 'receipt', 'recurring_frequency', 'recurring_end_date'],
                'budgets': ['user_id', 'notifications'],
                'savings_goals': ['user_id', 'priority'],
                'accounts': ['user_id'],
                'investment_portfolio': ['user_id', 'symbol', 'quantity', 'purchase_price'],
                'categories': ['user_id'],
                'tags': ['user_id'],
                'financial_goals': ['user_id'],
                'transaction_templates': ['user_id']
            }
            
            for table, columns in tables.items():
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"PRAGMA table_info({table})")
                    existing_columns = [col[1] for col in cursor.fetchall()]
                    
                    for column in columns:
                        if column not in existing_columns:
                            if column == 'user_id':
                                cursor.execute(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER')
                                if table == 'transactions':
                                    cursor.execute('''
                                        CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)
                                    ''')
                            elif column == 'category':
                                cursor.execute(f'ALTER TABLE {table} ADD COLUMN category TEXT NOT NULL DEFAULT "Other"')
                            elif column == 'notifications':
                                cursor.execute(f'ALTER TABLE {table} ADD COLUMN notifications BOOLEAN DEFAULT 1')
                            elif column == 'priority':
                                cursor.execute(f'ALTER TABLE {table} ADD COLUMN priority INTEGER DEFAULT 3')
                            else:
                                if column in ['amount', 'current_value', 'purchase_price']:
                                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} REAL')
                                elif column in ['recurring', 'notifications']:
                                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} BOOLEAN DEFAULT 0')
                                elif column in ['date', 'purchase_date', 'target_date', 'recurring_end_date']:
                                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} DATE')
                                else:
                                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} TEXT')
            
            # Enhanced default categories (limited to requested categories)
            default_categories = [
                ('Bills & Utilities', 'Expense'),
                ('Shopping', 'Expense'),
                ('Education', 'Expense'),
                ('Healthcare', 'Expense'),
                ('Entertainment', 'Expense'),
                ('Transportation', 'Expense')
            ]
            
            for category in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, type)
                    VALUES (?, ?)
                ''', category)
            
            cursor.execute("INSERT OR IGNORE INTO accounts (name, type, balance, currency) VALUES (?, ?, ?, ?)",
                         ("Cash", "Cash", 0, "IDR"))
            
            conn.commit()
        except Error as e:
            st.error(f"Failed to update database schema: {e}")
        finally:
            conn.close()

# ========== Transaction Functions ==========
def add_transaction(date, description, amount, category, trans_type, account="Cash", recurring=False, recurring_frequency=None, recurring_end_date=None, notes=None, tags=None, receipt=None, user_id=None):
    """Add a new transaction to the database."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (date, description, amount, category, type, account, recurring, recurring_frequency, recurring_end_date, notes, tags, receipt, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, description, amount, category or "Other", trans_type, account, int(recurring), recurring_frequency, recurring_end_date, notes, tags, receipt, user_id))
            conn.commit()
            st.success("Transaction added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add transaction: {e}")
            return False
        finally:
            conn.close()
    return False

def update_transaction(transaction_id, date, description, amount, category, trans_type, account, recurring, recurring_frequency, recurring_end_date, notes, tags, receipt, user_id):
    """Update an existing transaction."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET date = ?, description = ?, amount = ?, category = ?, type = ?, account = ?, recurring = ?, recurring_frequency = ?, recurring_end_date = ?, notes = ?, tags = ?, receipt = ?
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (date, description, amount, category or "Other", trans_type, account, int(recurring), recurring_frequency, recurring_end_date, notes, tags, receipt, transaction_id, user_id, user_id))
            conn.commit()
            st.success("Transaction updated successfully!")
            return True
        except Error as e:
            st.error(f"Failed to update transaction: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_transaction(transaction_id, user_id=None):
    """Delete a transaction."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transactions 
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (transaction_id, user_id, user_id))
            conn.commit()
            st.success("Transaction deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete transaction: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_all_transactions(user_id=None):
    """Delete all transactions for a user"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transactions 
                WHERE user_id = ? OR ? IS NULL
            ''', (user_id, user_id))
            conn.commit()
            st.success("All transactions deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete transactions: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_selected_transactions(transaction_ids, user_id=None):
    """Delete selected transactions"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(transaction_ids))
            query = f'''
                DELETE FROM transactions 
                WHERE id IN ({placeholders}) AND (user_id = ? OR ? IS NULL)
            '''
            params = transaction_ids + [user_id, user_id]
            cursor.execute(query, params)
            conn.commit()
            st.success(f"{cursor.rowcount} transactions deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete transactions: {e}")
            return False
        finally:
            conn.close()
    return False

def get_transactions(date_range=None, user_id=None):
    """Get transactions for the given date range and user."""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT id, date, description, amount, category, type, account, recurring, recurring_frequency, recurring_end_date, notes, tags
                FROM transactions
                WHERE (user_id = ? OR ? IS NULL)
            '''
            params = [user_id, user_id]
            
            if date_range and date_range[0] and date_range[1]:
                query += " AND date BETWEEN ? AND ?"
                params.extend([date_range[0], date_range[1]])
                
            query += " ORDER BY date DESC"
            
            df = pd.read_sql(query, conn, params=params, parse_dates=['date', 'recurring_end_date'])
            return df
        except Exception as e:
            st.error(f"Failed to get transactions: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def get_transaction_by_id(transaction_id, user_id=None):
    """Get a single transaction by ID."""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT id, date, description, amount, category, type, account, recurring, recurring_frequency, recurring_end_date, notes, tags, receipt
                FROM transactions
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            '''
            cursor = conn.cursor()
            cursor.execute(query, (transaction_id, user_id, user_id))
            result = cursor.fetchone()
            if result:
                columns = ['id', 'date', 'description', 'amount', 'category', 'type', 'account', 'recurring', 
                          'recurring_frequency', 'recurring_end_date', 'notes', 'tags', 'receipt']
                return dict(zip(columns, result))
            return None
        except Exception as e:
            st.error(f"Failed to get transaction: {e}")
            return None
        finally:
            conn.close()
    return None

def process_recurring_transactions(user_id=None):
    """Process recurring transactions and create new ones if needed."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            today = datetime.today().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT id, date, description, amount, category, type, account, recurring_frequency, recurring_end_date
                FROM transactions
                WHERE recurring = 1 AND (recurring_end_date IS NULL OR recurring_end_date >= ?)
                AND (user_id = ? OR ? IS NULL)
            ''', (today, user_id, user_id))
            
            recurring_transactions = cursor.fetchall()
            
            for trans in recurring_transactions:
                trans_id, last_date, description, amount, category, trans_type, account, frequency, end_date = trans
                last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                today_date = datetime.today().date()
                
                create_new = False
                next_date = None
                
                if frequency == 'Daily' and today_date > last_date:
                    create_new = True
                    next_date = last_date + timedelta(days=1)
                elif frequency == 'Weekly' and (today_date - last_date).days >= 7:
                    create_new = True
                    next_date = last_date + timedelta(weeks=1)
                elif frequency == 'Monthly':
                    next_month = last_date.month + 1
                    next_year = last_date.year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    
                    _, last_day = calendar.monthrange(next_year, next_month)
                    next_date = last_date.replace(year=next_year, month=next_month, day=min(last_date.day, last_day))
                    
                    if today_date >= next_date:
                        create_new = True
                elif frequency == 'Yearly':
                    next_date = last_date.replace(year=last_date.year + 1)
                    if today_date >= next_date:
                        create_new = True
                
                if create_new and next_date:
                    cursor.execute('''
                        INSERT INTO transactions (date, description, amount, category, type, account, recurring, recurring_frequency, recurring_end_date, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (next_date.strftime('%Y-%m-%d'), description, amount, category, trans_type, account, frequency, end_date, user_id))
            
            conn.commit()
        except Error as e:
            st.error(f"Failed to process recurring transactions: {e}")
        finally:
            conn.close()

def add_transaction_template(name, description, amount, category, trans_type, account, user_id=None):
    """Add a transaction template for quick entry"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transaction_templates (name, description, amount, category, type, account, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, amount, category, trans_type, account, user_id))
            conn.commit()
            st.success("Template saved successfully!")
            return True
        except Error as e:
            st.error(f"Failed to save template: {e}")
            return False
        finally:
            conn.close()
    return False

def get_transaction_templates(user_id=None):
    """Get all transaction templates for a user"""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT id, name, description, amount, category, type, account
                FROM transaction_templates
                WHERE user_id = ? OR ? IS NULL
                ORDER BY name
            '''
            df = pd.read_sql(query, conn, params=(user_id, user_id))
            return df
        except Exception as e:
            st.error(f"Failed to get templates: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def delete_transaction_template(template_id, user_id=None):
    """Delete a transaction template"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transaction_templates 
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (template_id, user_id, user_id))
            conn.commit()
            st.success("Template deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete template: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Accounts Functions ==========
def get_accounts(user_id=None):
    """Get all accounts for the user."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' in columns:
                query = '''
                    SELECT id, name, type, balance, currency, institution, account_number
                    FROM accounts
                    WHERE user_id = ? OR ? IS NULL
                    ORDER BY name
                '''
                params = (user_id, user_id)
            else:
                query = '''
                    SELECT id, name, type, balance, currency, institution, account_number
                    FROM accounts
                    ORDER BY name
                '''
                params = ()
                
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Failed to get accounts: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def add_account(name, account_type, balance, currency='IDR', institution=None, account_number=None, user_id=None):
    """Add a new account."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (name, type, balance, currency, institution, account_number, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, account_type, balance, currency, institution, account_number, user_id))
            conn.commit()
            st.success("Account added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add account: {e}")
            return False
        finally:
            conn.close()
    return False

def update_account_balance(account_name, amount, is_debit=False, user_id=None):
    """Update account balance after a transaction."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            if is_debit:
                cursor.execute('''
                    UPDATE accounts 
                    SET balance = balance - ?
                    WHERE name = ? AND (user_id = ? OR ? IS NULL)
                ''', (amount, account_name, user_id, user_id))
            else:
                cursor.execute('''
                    UPDATE accounts 
                    SET balance = balance + ?
                    WHERE name = ? AND (user_id = ? OR ? IS NULL)
                ''', (amount, account_name, user_id, user_id))
            conn.commit()
            return True
        except Error as e:
            st.error(f"Failed to update account balance: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Categories and Tags Functions ==========
def get_categories(trans_type=None, user_id=None):
    """Get all categories, optionally filtered by transaction type."""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT name, type 
                FROM categories
                WHERE (user_id = ? OR ? IS NULL)
            '''
            params = [user_id, user_id]
            
            if trans_type:
                query += " AND type = ?"
                params.append(trans_type)
                
            query += " ORDER BY name"
            
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Failed to get categories: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def add_category(name, trans_type, user_id=None):
    """Add a new category."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, type, user_id)
                VALUES (?, ?, ?)
            ''', (name, trans_type, user_id))
            conn.commit()
            st.success("Category added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add category: {e}")
            return False
        finally:
            conn.close()
    return False

def get_tags(user_id=None):
    """Get all tags."""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT name 
                FROM tags
                WHERE (user_id = ? OR ? IS NULL)
                ORDER BY name
            '''
            df = pd.read_sql(query, conn, params=(user_id, user_id))
            return df
        except Exception as e:
            st.error(f"Failed to get tags: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def add_tag(name, user_id=None):
    """Add a new tag."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tags (name, user_id)
                VALUES (?, ?)
            ''', (name, user_id))
            conn.commit()
            st.success("Tag added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add tag: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Savings Goals Functions ==========
def get_savings_goals(user_id=None):
    """Get all savings goals for the user."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(savings_goals)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' in columns:
                query = '''
                    SELECT id, name, target_amount, current_amount, target_date, notes, priority
                    FROM savings_goals
                    WHERE user_id = ? OR ? IS NULL
                    ORDER BY priority, target_date
                '''
                params = (user_id, user_id)
            else:
                query = '''
                    SELECT id, name, target_amount, current_amount, target_date, notes, priority
                    FROM savings_goals
                    ORDER BY priority, target_date
                '''
                params = ()
                
            df = pd.read_sql(query, conn, params=params, parse_dates=['target_date'])
            return df
        except Exception as e:
            st.error(f"Failed to get savings goals: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def add_savings_goal(name, target_amount, current_amount=0, target_date=None, notes=None, priority=3, user_id=None):
    """Add a new savings goal."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO savings_goals (name, target_amount, current_amount, target_date, notes, priority, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, target_amount, current_amount, target_date, notes, priority, user_id))
            conn.commit()
            st.success("Savings goal added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add savings goal: {e}")
            return False
        finally:
            conn.close()
    return False

def update_savings_goal(goal_id, name, target_amount, current_amount, target_date, notes, priority, user_id=None):
    """Update a savings goal."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE savings_goals 
                SET name = ?, target_amount = ?, current_amount = ?, target_date = ?, notes = ?, priority = ?
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (name, target_amount, current_amount, target_date, notes, priority, goal_id, user_id, user_id))
            conn.commit()
            st.success("Savings goal updated successfully!")
            return True
        except Error as e:
            st.error(f"Failed to update savings goal: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_savings_goal(goal_id, user_id=None):
    """Delete a savings goal."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM savings_goals 
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (goal_id, user_id, user_id))
            conn.commit()
            st.success("Savings goal deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete savings goal: {e}")
            return False
        finally:
            conn.close()
    return False

# ========== Investment Portfolio Functions ==========
def add_investment(name, investment_type, amount, purchase_date=None, current_value=None, symbol=None, quantity=None, purchase_price=None, notes=None, user_id=None):
    """Add a new investment to the portfolio"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investment_portfolio (name, type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, investment_type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes, user_id))
            conn.commit()
            st.success("Investment added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add investment: {e}")
            return False
        finally:
            conn.close()
    return False

def update_investment(investment_id, name, investment_type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes, user_id=None):
    """Update an existing investment."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE investment_portfolio 
                SET name = ?, type = ?, amount = ?, purchase_date = ?, current_value = ?, symbol = ?, quantity = ?, purchase_price = ?, notes = ?
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (name, investment_type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes, investment_id, user_id, user_id))
            conn.commit()
            st.success("Investment updated successfully!")
            return True
        except Error as e:
            st.error(f"Failed to update investment: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_investment(investment_id, user_id=None):
    """Delete an investment."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM investment_portfolio 
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (investment_id, user_id, user_id))
            conn.commit()
            st.success("Investment deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete investment: {e}")
            return False
        finally:
            conn.close()
    return False

def get_investments(user_id=None):
    """Get all investments"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(investment_portfolio)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' in columns:
                query = '''
                    SELECT id, name, type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes
                    FROM investment_portfolio
                    WHERE user_id = ? OR ? IS NULL
                    ORDER BY name
                '''
                params = (user_id, user_id)
            else:
                query = '''
                    SELECT id, name, type, amount, purchase_date, current_value, symbol, quantity, purchase_price, notes
                    FROM investment_portfolio
                    ORDER BY name
                '''
                params = ()
                
            df = pd.read_sql(query, conn, params=params, parse_dates=['purchase_date'])
            return df
        except Error as e:
            st.error(f"Failed to get investments: {e}")
        finally:
            conn.close()
    return pd.DataFrame()

def get_investment_performance(symbol, start_date, end_date):
    """Get investment performance data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        if not data.empty:
            return data['Close'].reset_index()
        return None
    except Exception as e:
        st.error(f"Failed to get investment data: {e}")
        return None

# ========== Budget Functions ==========
def get_budgets(month_year=None, user_id=None):
    """Get budgets for the given month/year or current month if not specified."""
    conn = create_connection()
    if conn is not None:
        try:
            if not month_year:
                today = datetime.today()
                month_year = today.strftime('%Y-%m')
            
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(budgets)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' in columns:
                query = '''
                    SELECT id, category, amount, month_year, notifications
                    FROM budgets
                    WHERE month_year = ? AND (user_id = ? OR ? IS NULL)
                    ORDER BY category
                '''
                params = (month_year, user_id, user_id)
            else:
                query = '''
                    SELECT id, category, amount, month_year, notifications
                    FROM budgets
                    WHERE month_year = ?
                    ORDER BY category
                '''
                params = (month_year,)
                
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Failed to get budgets: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def add_budget(category, amount, month_year=None, notifications=True, user_id=None):
    """Add a new budget."""
    conn = create_connection()
    if conn is not None:
        try:
            if not month_year:
                today = datetime.today()
                month_year = today.strftime('%Y-%m')
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO budgets (category, amount, month_year, notifications, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (category, amount, month_year, int(notifications), user_id))
            conn.commit()
            st.success("Budget added successfully!")
            return True
        except Error as e:
            st.error(f"Failed to add budget: {e}")
            return False
        finally:
            conn.close()
    return False

def update_budget(budget_id, category, amount, month_year, notifications, user_id=None):
    """Update a budget."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE budgets 
                SET category = ?, amount = ?, month_year = ?, notifications = ?
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (category, amount, month_year, int(notifications), budget_id, user_id, user_id))
            conn.commit()
            st.success("Budget updated successfully!")
            return True
        except Error as e:
            st.error(f"Failed to update budget: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_budget(budget_id, user_id=None):
    """Delete a budget."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM budgets 
                WHERE id = ? AND (user_id = ? OR ? IS NULL)
            ''', (budget_id, user_id, user_id))
            conn.commit()
            st.success("Budget deleted successfully!")
            return True
        except Error as e:
            st.error(f"Failed to delete budget: {e}")
            return False
        finally:
            conn.close()
    return False

def get_budget_vs_actual(month_year=None, user_id=None):
    """Compare budget vs actual spending for each category."""
    if not month_year:
        today = datetime.today()
        month_year = today.strftime('%Y-%m')
    
    budgets = get_budgets(month_year, user_id)
    if budgets.empty:
        return pd.DataFrame()
    
    # Get transactions for the month
    start_date = f"{month_year}-01"
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=31)).strftime('%Y-%m-%d')
    transactions = get_transactions((start_date, end_date), user_id)
    
    # Filter only expenses
    expenses = transactions[transactions['type'] == 'Expense']
    
    # Group by category and sum amounts
    if not expenses.empty:
        actual_spending = expenses.groupby('category')['amount'].sum().reset_index()
        actual_spending.columns = ['category', 'actual']
    else:
        actual_spending = pd.DataFrame(columns=['category', 'actual'])
    
    # Merge with budgets
    comparison = pd.merge(budgets, actual_spending, on='category', how='left')
    comparison['actual'] = comparison['actual'].fillna(0)
    comparison['difference'] = comparison['amount'] - comparison['actual']
    comparison['percentage'] = (comparison['actual'] / comparison['amount']) * 100
    
    return comparison

# ========== Utility Functions ==========
def format_currency(amount, currency='IDR'):
    """Format amount as currency with proper symbol"""
    if currency == 'IDR':
        return f"Rp {amount:,.0f}"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    elif currency == 'GBP':
        return f"£{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def get_date_range(period="This Month"):
    """Get date range based on selected period with more options"""
    today = datetime.today()
    
    if period == "Today":
        return (today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == "Yesterday":
        yesterday = today - timedelta(days=1)
        return (yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
    elif period == "This Week":
        start = today - timedelta(days=today.weekday())
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == "Last Week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == "This Month":
        start = today.replace(day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == "Last Month":
        first_day = today.replace(day=1)
        last_month_end = first_day - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return (last_month_start.strftime('%Y-%m-%d'), last_month_end.strftime('%Y-%m-%d'))
    elif period == "This Quarter":
        current_quarter = (today.month - 1) // 3 + 1
        quarter_start_month = 3 * current_quarter - 2
        start = today.replace(month=quarter_start_month, day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == "Last Quarter":
        current_quarter = (today.month - 1) // 3 + 1
        last_quarter = current_quarter - 1 if current_quarter > 1 else 4
        last_quarter_year = today.year if current_quarter > 1 else today.year - 1
        quarter_start_month = 3 * last_quarter - 2
        quarter_end_month = quarter_start_month + 2
        start = today.replace(year=last_quarter_year, month=quarter_start_month, day=1)
        end = today.replace(year=last_quarter_year, month=quarter_end_month, day=calendar.monthrange(last_quarter_year, quarter_end_month)[1])
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == "This Year":
        start = today.replace(month=1, day=1)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    elif period == "Last Year":
        start = today.replace(year=today.year-1, month=1, day=1)
        end = today.replace(year=today.year-1, month=12, day=31)
        return (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    elif period == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", today.replace(day=1))
        with col2:
            end_date = st.date_input("End date", today)
        return (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    return (None, None)

def get_financial_summary(date_range, user_id=None):
    """Return total income, expense, and balance for the given date range and user."""
    conn = create_connection()
    summary = {"income": 0, "expense": 0, "balance": 0}
    if conn is not None and date_range and date_range[0] and date_range[1]:
        try:
            query = '''
                SELECT 
                    SUM(CASE WHEN type = "Income" THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = "Expense" THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE date BETWEEN ? AND ?
            '''
            params = [date_range[0], date_range[1]]
            if user_id is not None:
                query += " AND (user_id = ? OR ? IS NULL)"
                params.extend([user_id, user_id])
            cur = conn.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            income = row[0] if row[0] is not None else 0
            expense = row[1] if row[1] is not None else 0
            summary = {
                "income": income,
                "expense": expense,
                "balance": income - expense
            }
        except Exception as e:
            st.error(f"Failed to get financial summary: {e}")
        finally:
            conn.close()
    return summary

def get_monthly_summary(year, user_id=None):
    """Return a DataFrame with monthly income and expense for the given year and user."""
    conn = create_connection()
    if conn is not None:
        try:
            query = '''
                SELECT 
                    strftime('%m', date) as month,
                    SUM(CASE WHEN type = "Income" THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = "Expense" THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE strftime('%Y', date) = ?
            '''
            params = [str(year)]
            if user_id is not None:
                query += " AND (user_id = ? OR ? IS NULL)"
                params.extend([user_id, user_id])
            query += " GROUP BY month ORDER BY month"
            df = pd.read_sql(query, conn, params=params)
            # Ensure all months are present
            months = [f"{i:02d}" for i in range(1, 13)]
            df = df.set_index('month').reindex(months, fill_value=0).reset_index()
            df['month'] = df['month'].apply(lambda x: calendar.month_abbr[int(x)])
            return df
        except Exception as e:
            st.error(f"Failed to get monthly summary: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def get_category_spending(date_range, user_id=None):
    """Get spending by category for the given date range."""
    conn = create_connection()
    if conn is not None and date_range and date_range[0] and date_range[1]:
        try:
            query = '''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type = "Expense" AND date BETWEEN ? AND ?
            '''
            params = [date_range[0], date_range[1]]
            if user_id is not None:
                query += " AND (user_id = ? OR ? IS NULL)"
                params.extend([user_id, user_id])
            query += " GROUP BY category ORDER BY total DESC"
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Failed to get category spending: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def get_account_balances(user_id=None):
    """Get current balances for all accounts."""
    accounts = get_accounts(user_id)
    if not accounts.empty:
        return accounts[['name', 'balance', 'currency']]
    return pd.DataFrame(columns=['name', 'balance', 'currency'])

def get_net_worth(user_id=None):
    """Calculate net worth (assets - liabilities)"""
    accounts = get_accounts(user_id)
    if not accounts.empty:
        return accounts['balance'].sum()
    return 0

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    try:
        c = CurrencyRates()
        rate = c.get_rate(from_currency, to_currency)
        return amount * rate
    except Exception as e:
        st.error(f"Failed to convert currency: {e}")
        return amount

def forecast_future_balances(transactions, months=6):
    """Forecast future account balances based on historical transactions"""
    try:
        transactions['date'] = pd.to_datetime(transactions['date'])
        transactions.set_index('date', inplace=True)
        
        monthly = transactions.resample('M')['amount'].sum()
        
        X = np.arange(len(monthly)).reshape(-1, 1)
        y = monthly.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_X = np.arange(len(monthly), len(monthly) + months).reshape(-1, 1)
        future_y = model.predict(future_X)
        
        last_date = monthly.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.MonthBegin(1),
            periods=months,
            freq='M'
        )
        
        forecast = pd.DataFrame({
            'date': future_dates,
            'amount': future_y
        })
        
        return forecast
    except Exception as e:
        st.error(f"Failed to generate forecast: {e}")
        return pd.DataFrame()

def analyze_spending_trends(transactions):
    """Analyze spending trends using time series decomposition"""
    try:
        transactions['date'] = pd.to_datetime(transactions['date'])
        transactions.set_index('date', inplace=True)
        
        monthly = transactions.resample('M')['amount'].sum()
        
        all_months = pd.date_range(
            start=monthly.index.min(),
            end=monthly.index.max(),
            freq='M'
        )
        monthly = monthly.reindex(all_months, fill_value=0)
        
        decomposition = seasonal_decompose(monthly, model='additive', period=12)
        
        return decomposition
    except Exception as e:
        st.error(f"Failed to analyze spending trends: {e}")
        return None

def calculate_next_occurrence(transaction):
    """Calculate next occurrence date for a recurring transaction"""
    last_date = pd.to_datetime(transaction['date'])
    frequency = transaction['recurring_frequency']
    
    if frequency == "Daily":
        return (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    elif frequency == "Weekly":
        return (last_date + timedelta(weeks=1)).strftime('%Y-%m-%d')
    elif frequency == "Monthly":
        return (last_date + pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    elif frequency == "Yearly":
        return (last_date + pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    return "N/A"

# ========== Data Import/Export Functions ==========
def export_transactions_to_csv(date_range=None, user_id=None):
    """Export transactions to CSV file"""
    transactions = get_transactions(date_range, user_id)
    if not transactions.empty:
        csv = transactions.to_csv(index=False)
        return csv
    return None

def export_transactions_to_excel(date_range=None, user_id=None):
    """Export transactions to Excel file"""
    transactions = get_transactions(date_range, user_id)
    if not transactions.empty:
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        transactions.to_excel(writer, index=False, sheet_name='Transactions')
        
        summary = transactions.groupby(['type', 'category', 'account'])['amount'].sum().unstack().fillna(0)
        summary.to_excel(writer, sheet_name='Summary')
        
        writer.close()
        output.seek(0)
        return output.getvalue()
    return None

def import_transactions_from_csv(file, user_id=None):
    """Import transactions from CSV file"""
    try:
        df = pd.read_csv(file)
        required_columns = ['date', 'description', 'amount', 'category', 'type']
        
        if not all(col in df.columns for col in required_columns):
            st.error(f"CSV file must contain these columns: {', '.join(required_columns)}")
            return False
        
        success_count = 0
        for _, row in df.iterrows():
            if add_transaction(
                row['date'],
                row['description'],
                row['amount'],
                row['category'],
                row['type'],
                row.get('account', 'Cash'),
                row.get('recurring', False),
                row.get('recurring_frequency'),
                row.get('recurring_end_date'),
                row.get('notes'),
                row.get('tags'),
                None,
                user_id
            ):
                success_count += 1
        
        st.success(f"Successfully imported {success_count} of {len(df)} transactions")
        return True
    except Exception as e:
        st.error(f"Failed to import transactions: {e}")
        return False

def backup_database():
    """Create a backup of the database file"""
    try:
        with open('finance.db', 'rb') as f:
            db_data = f.read()
        return db_data
    except Exception as e:
        st.error(f"Failed to create backup: {e}")
        return None

def restore_database(file):
    """Restore database from backup"""
    try:
        with open('finance.db', 'wb') as f:
            f.write(file.getvalue())
        st.success("Database restored successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to restore database: {e}")
        return False

# ========== Page Functions ==========
def dashboard_page(user_id=None):
    st.title("🏠 Dashboard")
    st.subheader("Welcome to your Finance Tracker Dashboard!")
    
    process_recurring_transactions(user_id)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        period = st.selectbox(
            "Select Period",
            ["This Month", "Last Month", "This Week", "Last Week", "This Quarter", "Last Quarter", "This Year", "Last Year", "Custom"],
            index=0,
            key="dashboard_period"
        )
    with col2:
        if period == "Custom":
            st.write("")
        else:
            refresh = st.button("🔄 Refresh", help="Refresh dashboard data")
    
    date_range = get_date_range(period)
    summary = get_financial_summary(date_range, user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", format_currency(summary["income"]))
    with col2:
        st.metric("Total Expenses", format_currency(summary["expense"]))
    with col3:
        st.metric("Net Balance", format_currency(summary["balance"]))
    with col4:
        st.metric("Net Worth", format_currency(get_net_worth(user_id)))
    
    st.markdown("---")
    
    # Daily Spending Trend Chart
    st.subheader("Daily Spending Trend")
    transactions = get_transactions(date_range, user_id)
    daily_expenses = transactions[transactions['type'] == 'Expense'].groupby('date')['amount'].sum().reset_index()
    
    if not daily_expenses.empty:
        fig = px.line(
            daily_expenses,
            x='date',
            y='amount',
            title="Daily Expense Trend",
            markers=True,
            labels={'amount': 'Amount (Rp)', 'date': 'Date'}
        )
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Amount (Rp)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available for daily trend")
    
    st.subheader("Monthly Trends")
    monthly_data = get_monthly_summary(datetime.today().year, user_id)
    if not monthly_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_data['month'],
            y=monthly_data['income'],
            name='Income',
            marker_color='#2ecc71'
        ))
        fig.add_trace(go.Bar(
            x=monthly_data['month'],
            y=monthly_data['expense'],
            name='Expense',
            marker_color='#e74c3c'
        ))
        fig.update_layout(
            barmode='group',
            hovermode="x unified",
            yaxis_title="Amount (IDR)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction data available for this period")
    
    st.subheader("Spending by Category")
    category_spending = get_category_spending(date_range, user_id)
    if not category_spending.empty:
        fig = px.pie(
            category_spending,
            names='category',
            values='total',
            hole=0.4,
            title="Expense Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available for this period")
    
    st.subheader("Account Balances")
    accounts = get_account_balances(user_id)
    if not accounts.empty:
        fig = px.bar(
            accounts,
            x='name',
            y='balance',
            color='name',
            text='balance',
            title="Current Account Balances"
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No account data available")

def transactions_page(user_id=None):
    st.title("💸 Transactions")
    
    # Add a new tab layout for different transaction views
    tab1, tab2, tab3 = st.tabs(["Transaction Records", "Recurring Transactions", "Transaction Analysis"])
    
    with tab1:
        st.subheader("Transaction Records")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            period = st.selectbox(
                "Select Period",
                ["This Month", "Last Month", "This Week", "Last Week", "This Year", "Last Year", "Custom"],
                index=0,
                key="transactions_period"
            )
        with col2:
            if period == "Custom":
                st.write("")
            else:
                if st.button("🔄 Refresh", key="refresh_transactions"):
                    st.rerun()
        
        date_range = get_date_range(period)
        transactions = get_transactions(date_range, user_id)
        
        # Add quick filters
        with st.expander("🔍 Filter Transactions", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.selectbox("Type", ["All", "Income", "Expense"])
            with col2:
                filter_category = st.selectbox("Category", ["All"] + get_categories(user_id=user_id)['name'].unique().tolist())
            with col3:
                filter_account = st.selectbox("Account", ["All"] + get_accounts(user_id=user_id)['name'].unique().tolist())
            
            if filter_type != "All":
                transactions = transactions[transactions['type'] == filter_type]
            if filter_category != "All":
                transactions = transactions[transactions['category'] == filter_category]
            if filter_account != "All":
                transactions = transactions[transactions['account'] == filter_account]
        
        # Add transaction statistics
        if not transactions.empty:
            total_income = transactions[transactions['type'] == 'Income']['amount'].sum()
            total_expense = transactions[transactions['type'] == 'Expense']['amount'].sum()
            net_balance = total_income - total_expense
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", format_currency(total_income))
            with col2:
                st.metric("Total Expenses", format_currency(total_expense))
            with col3:
                st.metric("Net Balance", format_currency(net_balance))
        
        # Enhanced transaction table with editable fields
        if not transactions.empty:
            # Convert DataFrame to editable format
            edited_df = st.data_editor(
                transactions.drop(columns=['id']),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "date": st.column_config.DateColumn("Date"),
                    "amount": st.column_config.NumberColumn("Amount", format="Rp %d"),
                    "type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"]),
                    "category": st.column_config.SelectboxColumn(
                        "Category",
                        options=get_categories(user_id=user_id)['name'].unique().tolist()
                    ),
                    "account": st.column_config.SelectboxColumn(
                        "Account",
                        options=get_accounts(user_id=user_id)['name'].unique().tolist()
                    )
                }
            )
            
            # Add delete functionality
            st.markdown("---")
            st.subheader("Delete Transactions")
            
            # Option 1: Delete selected transactions
            selected_indices = st.multiselect(
                "Select transactions to delete",
                options=transactions.index,
                format_func=lambda x: f"{transactions.loc[x, 'date']} - {transactions.loc[x, 'description']} - {format_currency(transactions.loc[x, 'amount'])}"
            )
            
            if selected_indices and st.button("🗑️ Delete Selected", type="primary"):
                transaction_ids = transactions.loc[selected_indices, 'id'].tolist()
                if delete_selected_transactions(transaction_ids, user_id):
                    st.rerun()
            
            # Option 2: Delete all transactions in current view
            st.warning("Danger Zone")
            if st.button("💣 Delete ALL Transactions in Current View", type="secondary"):
                if st.checkbox("I understand this will permanently delete all transactions in the current view"):
                    transaction_ids = transactions['id'].tolist()
                    if delete_selected_transactions(transaction_ids, user_id):
                        st.rerun()
            
            # Export options
            st.download_button(
                label="📥 Export to CSV",
                data=edited_df.to_csv(index=False).encode('utf-8'),
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No transactions found for the selected period")
    
    with tab2:
        st.subheader("Recurring Transactions")
        
        # Show existing recurring transactions
        recurring_trans = get_transactions(user_id=user_id)
        recurring_trans = recurring_trans[recurring_trans['recurring'] == True]
        
        if not recurring_trans.empty:
            for _, trans in recurring_trans.iterrows():
                with st.expander(f"{trans['description']} - {format_currency(trans['amount'])}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Frequency:** {trans['recurring_frequency']}")
                        st.write(f"**Next Occurrence:** {calculate_next_occurrence(trans)}")
                    with col2:
                        st.write(f"**Category:** {trans['category']}")
                        st.write(f"**Account:** {trans['account']}")
                    
                    if st.button("Edit", key=f"edit_{trans['id']}"):
                        st.session_state['edit_recurring'] = trans['id']
                    
                    if st.button("Delete", key=f"delete_{trans['id']}"):
                        if delete_transaction(trans['id'], user_id):
                            st.rerun()
        else:
            st.info("No recurring transactions found")
        
        # Add new recurring transaction form
        with st.expander("➕ Add New Recurring Transaction", expanded='edit_recurring' in st.session_state):
            if 'edit_recurring' in st.session_state:
                edit_trans = recurring_trans[recurring_trans['id'] == st.session_state['edit_recurring']].iloc[0]
            else:
                edit_trans = None
            
            with st.form(key='recurring_trans_form'):
                col1, col2 = st.columns(2)
                with col1:
                    description = st.text_input("Description", value=edit_trans['description'] if edit_trans else "")
                    amount = st.number_input("Amount", min_value=0.01, value=edit_trans['amount'] if edit_trans else 0.01)
                    frequency = st.selectbox(
                        "Frequency",
                        ["Daily", "Weekly", "Monthly", "Yearly"],
                        index=["Daily", "Weekly", "Monthly", "Yearly"].index(edit_trans['recurring_frequency']) if edit_trans else 0
                    )
                with col2:
                    category = st.selectbox(
                        "Category",
                        options=get_categories(user_id=user_id)['name'].unique().tolist(),
                        index=get_categories(user_id=user_id)['name'].unique().tolist().index(edit_trans['category']) if edit_trans else 0
                    )
                    account = st.selectbox(
                        "Account",
                        options=get_accounts(user_id=user_id)['name'].unique().tolist(),
                        index=get_accounts(user_id=user_id)['name'].unique().tolist().index(edit_trans['account']) if edit_trans else 0
                    )
                    end_date = st.date_input("End Date (optional)", value=pd.to_datetime(edit_trans['recurring_end_date']) if edit_trans and edit_trans['recurring_end_date'] else None)
                
                if st.form_submit_button("💾 Save Recurring Transaction"):
                    if edit_trans:
                        # Update existing transaction
                        if update_transaction(
                            edit_trans['id'],
                            edit_trans['date'],
                            description,
                            amount,
                            category,
                            edit_trans['type'],
                            account,
                            True,
                            frequency,
                            end_date.strftime('%Y-%m-%d') if end_date else None,
                            edit_trans.get('notes'),
                            edit_trans.get('tags'),
                            None,
                            user_id
                        ):
                            del st.session_state['edit_recurring']
                            st.rerun()
                    else:
                        # Add new transaction
                        if add_transaction(
                            datetime.today().strftime('%Y-%m-%d'),
                            description,
                            amount,
                            category,
                            "Expense",  # Assuming recurring transactions are expenses
                            account,
                            True,
                            frequency,
                            end_date.strftime('%Y-%m-%d') if end_date else None,
                            None,
                            None,
                            None,
                            user_id
                        ):
                            st.rerun()
    
    with tab3:
        st.subheader("Transaction Analysis")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", datetime.today())
        
        # Get transactions for analysis
        analysis_trans = get_transactions((start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), user_id)
        
        if not analysis_trans.empty:
            # Spending by category chart
            st.subheader("Spending by Category")
            spending_by_cat = analysis_trans[analysis_trans['type'] == 'Expense'].groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                spending_by_cat,
                names='category',
                values='amount',
                hole=0.4,
                title=f"Spending Distribution ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily spending trend
            st.subheader("Daily Spending Trend")
            daily_spending = analysis_trans[analysis_trans['type'] == 'Expense'].groupby('date')['amount'].sum().reset_index()
            fig = px.line(
                daily_spending,
                x='date',
                y='amount',
                title="Daily Spending Over Time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Top expenses
            st.subheader("Top Expenses")
            top_expenses = analysis_trans[analysis_trans['type'] == 'Expense'].nlargest(10, 'amount')
            st.dataframe(top_expenses[['date', 'description', 'category', 'amount']], use_container_width=True)
        else:
            st.info("No transactions available for analysis in this period")

def budgets_page(user_id=None):
    st.title("📅 Budgets")
    
    today = datetime.today()
    current_month_year = today.strftime('%Y-%m')
    months = [f"{today.year}-{m:02d}" for m in range(1, 13)]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        month_year = st.selectbox(
            "Select Month/Year",
            options=months,
            index=months.index(current_month_year)
        )
    with col2:
        st.write("")
    
    comparison = get_budget_vs_actual(month_year, user_id)
    
    if not comparison.empty:
        st.subheader("Budget vs Actual Spending")
        
        comparison['utilization'] = (comparison['actual'] / comparison['amount']) * 100
        comparison['status'] = comparison['utilization'].apply(
            lambda x: "Over" if x > 100 else "Under" if x < 100 else "On Target"
        )
        
        def color_status(val):
            color = 'red' if val == "Over" else 'green' if val == "Under" else 'orange'
            return f'color: {color}'
        
        st.dataframe(
            comparison.style.applymap(color_status, subset=['status']),
            use_container_width=True
        )
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=comparison['category'],
            y=comparison['amount'],
            name='Budget',
            marker_color='#3498db'
        ))
        fig.add_trace(go.Bar(
            x=comparison['category'],
            y=comparison['actual'],
            name='Actual',
            marker_color='#e74c3c'
        ))
        fig.update_layout(
            barmode='group',
            hovermode="x unified",
            yaxis_title="Amount (IDR)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No budgets set for this month")
    
    with st.expander("➕ Add/Edit Budget", expanded=False):
        budgets = get_budgets(month_year, user_id)
        existing_categories = budgets['category'].tolist() if not budgets.empty else []
        expense_categories = get_categories('Expense', user_id)['name'].tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Category",
                options=[c for c in expense_categories if c not in existing_categories] if expense_categories else ["Other"],
                key="budget_category"
            )
        with col2:
            amount = st.number_input("Amount (Rp)", min_value=0, step=10000, key="budget_amount")
        
        notifications = st.checkbox("Enable notifications", value=True, key="budget_notifications")
        
        if st.button("💾 Save Budget"):
            if category and amount > 0:
                if add_budget(category, amount, month_year, notifications, user_id):
                    st.rerun()
            else:
                st.error("Please select a category and enter an amount")

def savings_goals_page(user_id=None):
    st.title("🎯 Savings Goals")
    
    goals = get_savings_goals(user_id)
    
    if not goals.empty:
        for _, goal in goals.iterrows():
            progress = (goal['current_amount'] / goal['target_amount']) * 100
            days_left = (goal['target_date'] - datetime.today().date()).days if goal['target_date'] else None
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(goal['name'])
                    st.caption(f"Target: {format_currency(goal['target_amount'])} • Current: {format_currency(goal['current_amount'])}")
                    
                    st.progress(min(progress / 100, 1.0))
                    
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Progress", f"{progress:.1f}%")
                    with cols[1]:
                        st.metric("Remaining", format_currency(goal['target_amount'] - goal['current_amount']))
                    with cols[2]:
                        if days_left is not None:
                            st.metric("Days Left", days_left)
                
                with col2:
                    with st.popover("⚙️ Actions"):
                        if st.button("Add Funds", key=f"add_{goal['id']}"):
                            st.session_state['edit_goal_id'] = goal['id']
                            st.session_state['edit_goal_action'] = 'add'
                        
                        if st.button("Edit", key=f"edit_{goal['id']}"):
                            st.session_state['edit_goal_id'] = goal['id']
                            st.session_state['edit_goal_action'] = 'edit'
                        
                        if st.button("Delete", key=f"delete_{goal['id']}"):
                            if delete_savings_goal(goal['id'], user_id):
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("You don't have any savings goals yet")
    
    with st.expander("➕ Add New Savings Goal", expanded='edit_goal_id' in st.session_state):
        if 'edit_goal_id' in st.session_state:
            goal = goals[goals['id'] == st.session_state['edit_goal_id']].iloc[0]
            action = st.session_state['edit_goal_action']
        else:
            goal = None
            action = None
        
        with st.form(key='savings_goal_form'):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Goal Name", value=goal['name'] if goal else "")
                target_amount = st.number_input(
                    "Target Amount (Rp)",
                    min_value=0,
                    step=10000,
                    value=goal['target_amount'] if goal else 0
                )
                priority = st.select_slider(
                    "Priority",
                    options=[1, 2, 3, 4, 5],
                    value=goal['priority'] if goal else 3
                )
            with col2:
                if action == 'add':
                    current_amount = st.number_input(
                        "Amount to Add (Rp)",
                        min_value=0,
                        step=10000,
                        value=0
                    )
                else:
                    current_amount = st.number_input(
                        "Current Amount (Rp)",
                        min_value=0,
                        step=10000,
                        value=goal['current_amount'] if goal else 0
                    )
                target_date = st.date_input(
                    "Target Date",
                    value=goal['target_date'] if goal and goal['target_date'] else datetime.today() + timedelta(days=30)
                )
                notes = st.text_area(
                    "Notes",
                    value=goal['notes'] if goal and goal['notes'] else ""
                )
            
            if st.form_submit_button("💾 Save Goal"):
                if name and target_amount > 0:
                    if goal and action == 'edit':
                        if update_savings_goal(
                            goal['id'],
                            name,
                            target_amount,
                            current_amount,
                            target_date,
                            notes,
                            priority,
                            user_id
                        ):
                            del st.session_state['edit_goal_id']
                            del st.session_state['edit_goal_action']
                            st.rerun()
                    elif goal and action == 'add':
                        if update_savings_goal(
                            goal['id'],
                            goal['name'],
                            goal['target_amount'],
                            goal['current_amount'] + current_amount,
                            goal['target_date'],
                            goal['notes'],
                            goal['priority'],
                            user_id
                        ):
                            del st.session_state['edit_goal_id']
                            del st.session_state['edit_goal_action']
                            st.rerun()
                    else:
                        if add_savings_goal(
                            name,
                            target_amount,
                            current_amount,
                            target_date,
                            notes,
                            priority,
                            user_id
                        ):
                            st.rerun()
                else:
                    st.error("Please enter a name and target amount")

def accounts_page(user_id=None):
    st.title("🏦 Accounts")
    
    accounts = get_accounts(user_id)
    
    with st.expander("➕ Add New Account", expanded=False):
        with st.form(key='account_form'):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Account Name")
                account_type = st.selectbox(
                    "Account Type",
                    ["Cash", "Bank", "Credit Card", "Investment", "Loan", "Other"]
                )
                balance = st.number_input("Initial Balance (Rp)", min_value=0, step=10000)
            with col2:
                currency = st.selectbox(
                    "Currency",
                    ["IDR", "USD", "EUR", "GBP", "SGD", "AUD", "JPY"]
                )
                institution = st.text_input("Institution (optional)")
                account_number = st.text_input("Account Number (optional)")
            
            if st.form_submit_button("💾 Save Account"):
                if name and balance >= 0:
                    if add_account(
                        name,
                        account_type,
                        balance,
                        currency,
                        institution,
                        account_number,
                        user_id
                    ):
                        st.rerun()
                else:
                    st.error("Please enter an account name and valid balance")
    
    if not accounts.empty:
        gb = GridOptionsBuilder.from_dataframe(accounts)
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            resizable=True,
            editable=False,
            wrapText=True,
            autoHeight=True
        )
        
        gb.configure_column("id", hide=True)
        gb.configure_column("balance", type=["numericColumn", "numberColumnFilter"], valueFormatter="value.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', maximumFractionDigits: 0})")
        
        gb.configure_column(
            "Actions", 
            cellRenderer=JsCode('''
                function(params) {
                    let actions = document.createElement('div');
                    actions.style.display = 'flex';
                    actions.style.gap = '5px';
                    
                    let editBtn = document.createElement('button');
                    editBtn.textContent = '✏️';
                    editBtn.style.border = 'none';
                    editBtn.style.background = 'none';
                    editBtn.style.cursor = 'pointer';
                    editBtn.onclick = () => {
                        window.parent.postMessage({
                            'type': 'editAccount',
                            'id': params.data.id
                        }, '*');
                    };
                    
                    let deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '🗑️';
                    deleteBtn.style.border = 'none';
                    deleteBtn.style.background = 'none';
                    deleteBtn.style.cursor = 'pointer';
                    deleteBtn.onclick = () => {
                        if (confirm('Are you sure you want to delete this account?')) {
                            window.parent.postMessage({
                                'type': 'deleteAccount',
                                'id': params.data.id
                            }, '*');
                        }
                    };
                    
                    actions.appendChild(editBtn);
                    actions.appendChild(deleteBtn);
                    return actions;
                }
            '''),
            lockPosition='right',
            width=100
        )
        
        grid_options = gb.build()
        
        try:
            grid_response = AgGrid(
                accounts,
                gridOptions=grid_options,
                height=400,
                width='100%',
                theme='streamlit',
                update_mode='MODEL_CHANGED',
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                key=f'accounts_grid_{user_id}' if user_id else 'accounts_grid',
                try_to_convert_back_to_original_types=False
            )
            
            selected_rows = grid_response['selected_rows']
            
            if selected_rows:
                st.subheader("Selected Accounts")
                selected_df = pd.DataFrame(selected_rows)
                selected_df = selected_df[[col for col in selected_df.columns if not col.startswith('_')]]
                st.dataframe(selected_df, use_container_width=True)
                
                if st.button("🗑️ Delete Selected Accounts", type="primary"):
                    if delete_selected_transactions([row['id'] for row in selected_rows], user_id):
                        st.rerun()
        except Exception as e:
            st.error(f"Error displaying accounts grid: {e}")
            st.dataframe(accounts, use_container_width=True)
    else:
        st.info("No accounts found")

def investments_page(user_id=None):
    st.title("📈 Investment Portfolio")
    
    tab1, tab2, tab3 = st.tabs(["View Investments", "Add Investment", "Investment Analysis"])
    
    with tab1:
        st.subheader("Your Investment Portfolio")
        investments = get_investments(user_id)
        
        if not investments.empty:
            investments['roi'] = ((investments['current_value'] - investments['amount']) / investments['amount']) * 100
            
            gb = GridOptionsBuilder.from_dataframe(investments)
            gb.configure_default_column(
                filterable=True,
                sortable=True,
                resizable=True,
                editable=False,
                wrapText=True,
                autoHeight=True
            )
            
            gb.configure_column("id", hide=True)
            gb.configure_column("purchase_date", type=["dateColumnFilter", "customDateTimeFormat"], custom_format_string='yyyy-MM-dd')
            gb.configure_column("amount", type=["numericColumn", "numberColumnFilter"], valueFormatter="value.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', maximumFractionDigits: 0})")
            gb.configure_column("current_value", type=["numericColumn", "numberColumnFilter"], valueFormatter="value.toLocaleString('id-ID', {style: 'currency', currency: 'IDR', maximumFractionDigits: 0})")
            gb.configure_column("roi", type=["numericColumn", "numberColumnFilter"], valueFormatter="value.toFixed(2) + '%'")
            
            gb.configure_column(
                "Actions", 
                cellRenderer=JsCode('''
                    function(params) {
                        let actions = document.createElement('div');
                        actions.style.display = 'flex';
                        actions.style.gap = '5px';
                        
                        let editBtn = document.createElement('button');
                        editBtn.textContent = '✏️';
                        editBtn.style.border = 'none';
                        editBtn.style.background = 'none';
                        editBtn.style.cursor = 'pointer';
                        editBtn.onclick = () => {
                            window.parent.postMessage({
                                'type': 'editInvestment',
                                'id': params.data.id
                            }, '*');
                        };
                        
                        let deleteBtn = document.createElement('button');
                        deleteBtn.textContent = '🗑️';
                        deleteBtn.style.border = 'none';
                        deleteBtn.style.background = 'none';
                        deleteBtn.style.cursor = 'pointer';
                        deleteBtn.onclick = () => {
                            if (confirm('Are you sure you want to delete this investment?')) {
                                window.parent.postMessage({
                                    'type': 'deleteInvestment',
                                    'id': params.data.id
                                }, '*');
                            }
                        };
                        
                        actions.appendChild(editBtn);
                        actions.appendChild(deleteBtn);
                        return actions;
                    }
                '''),
                lockPosition='right',
                width=100
            )
            
            grid_options = gb.build()
            
            try:
                grid_response = AgGrid(
                    investments,
                    gridOptions=grid_options,
                    height=500,
                    width='100%',
                    theme='streamlit',
                    update_mode='MODEL_CHANGED',
                    allow_unsafe_jscode=True,
                    fit_columns_on_grid_load=True,
                    key=f'investments_grid_{user_id}' if user_id else 'investments_grid',
                    try_to_convert_back_to_original_types=False
                )
                
                selected_rows = grid_response['selected_rows']
                
                if selected_rows:
                    st.subheader("Selected Investments")
                    selected_df = pd.DataFrame(selected_rows)
                    selected_df = selected_df[[col for col in selected_df.columns if not col.startswith('_')]]
                    st.dataframe(selected_df, use_container_width=True)
                    
                    if st.button("🗑️ Delete Selected Investments", type="primary"):
                        if delete_selected_transactions([row['id'] for row in selected_rows], user_id):
                            st.rerun()
            except Exception as e:
                st.error(f"Error displaying investments grid: {e}")
                st.dataframe(investments, use_container_width=True)
        else:
            st.info("You don't have any investments recorded yet")
    
    with tab2:
        st.subheader("Add New Investment")
        with st.form(key='investment_form'):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Investment Name*", placeholder="e.g., Apple Stock")
                investment_type = st.selectbox(
                    "Investment Type*",
                    ["Stock", "Bond", "Mutual Fund", "ETF", "Real Estate", "Crypto", "Other"]
                )
                symbol = st.text_input("Symbol/Ticker (optional)", placeholder="e.g., AAPL")
                amount = st.number_input("Amount Invested* (Rp)", min_value=0, step=10000)
                purchase_date = st.date_input("Purchase Date", datetime.today())
            with col2:
                quantity = st.number_input("Quantity (optional)", min_value=0.0, step=1.0, format="%.2f")
                purchase_price = st.number_input("Purchase Price (optional)", min_value=0.0, step=0.01, format="%.2f")
                current_value = st.number_input("Current Value (Rp)", min_value=0, step=10000, value=amount)
                notes = st.text_area("Notes")
            
            if st.form_submit_button("💾 Save Investment"):
                if name and amount > 0:
                    if add_investment(
                        name,
                        investment_type,
                        amount,
                        purchase_date.strftime('%Y-%m-%d'),
                        current_value,
                        symbol,
                        quantity,
                        purchase_price,
                        notes,
                        user_id
                    ):
                        st.rerun()
                else:
                    st.error("Please fill all required fields (marked with *)")
    
    with tab3:
        st.subheader("Investment Analysis")
        investments = get_investments(user_id)
        
        if not investments.empty:
            total_invested = investments['amount'].sum()
            total_current = investments['current_value'].sum()
            profit_loss = total_current - total_invested
            roi = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Invested", format_currency(total_invested))
            with col2:
                st.metric("Current Value", format_currency(total_current))
            with col3:
                st.metric("Profit/Loss", 
                         format_currency(profit_loss),
                         f"{roi:.2f}% ROI",
                         delta_color="inverse" if profit_loss < 0 else "normal")
            
            st.subheader("Investment Type Distribution")
            type_dist = investments.groupby('type')['amount'].sum().reset_index()
            fig = px.pie(
                type_dist,
                names='type',
                values='amount',
                hole=0.4,
                title="Investment by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            if not investments[investments['symbol'].notna()].empty:
                st.subheader("Market Performance")
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        datetime.today() - timedelta(days=365),
                        key="perf_start_date"
                    )
                with col2:
                    end_date = st.date_input(
                        "End Date",
                        datetime.today(),
                        key="perf_end_date"
                    )
                
                performance_data = {}
                for _, investment in investments[investments['symbol'].notna()].iterrows():
                    data = get_investment_performance(
                        investment['symbol'],
                        start_date.strftime('%Y-%m-%d'),
                        (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    )
                    if data is not None:
                        performance_data[investment['name']] = data
                
                if performance_data:
                    fig = go.Figure()
                    for name, data in performance_data.items():
                        fig.add_trace(go.Scatter(
                            x=data['Date'],
                            y=data['Close'],
                            name=name,
                            mode='lines'
                        ))
                    
                    fig.update_layout(
                        title="Investment Performance Over Time",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Could not fetch performance data for these investments")
        else:
            st.info("No investments to analyze")

def reports_page(user_id=None):
    st.title("📊 Financial Reports")
    
    tab1, tab2, tab3 = st.tabs(["Spending Analysis", "Income Analysis", "Custom Reports"])
    
    with tab1:
        st.subheader("Spending Analysis")
        
        period = st.selectbox(
            "Select Period",
            ["This Month", "Last Month", "This Year", "Last Year", "Custom"],
            index=0,
            key="spending_period"
        )
        date_range = get_date_range(period)
        
        spending = get_category_spending(date_range, user_id)
        
        if not spending.empty:
            st.subheader("Spending by Category")
            fig = px.pie(
                spending,
                names='category',
                values='total',
                hole=0.4,
                title=f"Spending Distribution ({period})"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Monthly Spending Trends")
            monthly_spending = get_monthly_summary(datetime.today().year, user_id)
            if not monthly_spending.empty:
                fig = px.line(
                    monthly_spending,
                    x='month',
                    y='expense',
                    title="Monthly Spending Over Time",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Amount (IDR)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Spending Forecast")
            transactions = get_transactions(date_range, user_id)
            expenses = transactions[transactions['type'] == 'Expense']
            
            if not expenses.empty:
                forecast = forecast_future_balances(expenses)
                if not forecast.empty:
                    fig = px.line(
                        forecast,
                        x='date',
                        y='amount',
                        title="6-Month Spending Forecast",
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Amount (IDR)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Spending Trends Analysis")
                decomposition = analyze_spending_trends(expenses)
                if decomposition:
                    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 8))
                    
                    decomposition.observed.plot(ax=ax1)
                    ax1.set_ylabel('Observed')
                    
                    decomposition.trend.plot(ax=ax2)
                    ax2.set_ylabel('Trend')
                    
                    decomposition.seasonal.plot(ax=ax3)
                    ax3.set_ylabel('Seasonal')
                    
                    decomposition.resid.plot(ax=ax4)
                    ax4.set_ylabel('Residual')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
        else:
            st.info("No spending data available for this period")
    
    with tab2:
        st.subheader("Income Analysis")
        
        period = st.selectbox(
            "Select Period",
            ["This Month", "Last Month", "This Year", "Last Year", "Custom"],
            index=0,
            key="income_period"
        )
        date_range = get_date_range(period)
        
        transactions = get_transactions(date_range, user_id)
        income = transactions[transactions['type'] == 'Income']
        
        if not income.empty:
            st.subheader("Income by Category")
            income_by_category = income.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                income_by_category,
                names='category',
                values='amount',
                hole=0.4,
                title=f"Income Distribution ({period})"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Monthly Income Trends")
            monthly_income = get_monthly_summary(datetime.today().year, user_id)
            if not monthly_income.empty:
                fig = px.line(
                    monthly_income,
                    x='month',
                    y='income',
                    title="Monthly Income Over Time",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Amount (IDR)"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No income data available for this period")
    
    with tab3:
        st.subheader("Custom Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", datetime.today())
        
        date_range = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        report_type = st.selectbox(
            "Report Type",
            ["Transaction Summary", "Category Breakdown", "Account Summary", "Net Worth Trend"]
        )
        
        if st.button("Generate Report"):
            if report_type == "Transaction Summary":
                transactions = get_transactions(date_range, user_id)
                if not transactions.empty:
                    st.subheader("Transaction Summary")
                    st.dataframe(
                        transactions.groupby(['type', 'category', 'account'])['amount'].sum().unstack().fillna(0),
                        use_container_width=True
                    )
                else:
                    st.info("No transactions in this period")
            
            elif report_type == "Category Breakdown":
                st.subheader("Category Breakdown")
                
                transactions = get_transactions(date_range, user_id)
                income = transactions[transactions['type'] == 'Income']
                expenses = transactions[transactions['type'] == 'Expense']
                
                if not income.empty or not expenses.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        if not income.empty:
                            st.write("Income by Category")
                            income_by_cat = income.groupby('category')['amount'].sum().sort_values(ascending=False)
                            st.dataframe(income_by_cat, use_container_width=True)
                        else:
                            st.info("No income in this period")
                    
                    with col2:
                        if not expenses.empty:
                            st.write("Expenses by Category")
                            expenses_by_cat = expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
                            st.dataframe(expenses_by_cat, use_container_width=True)
                        else:
                            st.info("No expenses in this period")
                else:
                    st.info("No transactions in this period")
            
            elif report_type == "Account Summary":
                st.subheader("Account Summary")
                
                accounts = get_accounts(user_id)
                transactions = get_transactions(date_range, user_id)
                
                if not accounts.empty:
                    account_summary = []
                    for _, account in accounts.iterrows():
                        account_trans = transactions[transactions['account'] == account['name']]
                        inflows = account_trans[account_trans['type'] == 'Income']['amount'].sum()
                        outflows = account_trans[account_trans['type'] == 'Expense']['amount'].sum()
                        
                        account_summary.append({
                            'Account': account['name'],
                            'Type': account['type'],
                            'Starting Balance': account['balance'] - inflows + outflows,
                            'Inflows': inflows,
                            'Outflows': outflows,
                            'Ending Balance': account['balance'],
                            'Currency': account['currency']
                        })
                    
                    st.dataframe(pd.DataFrame(account_summary), use_container_width=True)
                else:
                    st.info("No accounts found")
            
            elif report_type == "Net Worth Trend":
                st.subheader("Net Worth Trend")
                
                transactions = get_transactions(date_range, user_id)
                accounts = get_accounts(user_id)
                
                if not transactions.empty and not accounts.empty:
                    transactions['date'] = pd.to_datetime(transactions['date'])
                    transactions['month'] = transactions['date'].dt.to_period('M')
                    
                    monthly_changes = transactions.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
                    monthly_changes['net'] = monthly_changes.get('Income', 0) - monthly_changes.get('Expense', 0)
                    
                    monthly_changes['net_worth'] = monthly_changes['net'].cumsum()
                    
                    fig = px.line(
                        monthly_changes.reset_index(),
                        x=monthly_changes.reset_index()['month'].astype(str),
                        y='net_worth',
                        title="Net Worth Over Time",
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Net Worth (IDR)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough data to calculate net worth trend")

def data_management_page(user_id=None):
    st.title("🗄️ Data Management")
    
    tab1, tab2, tab3 = st.tabs(["Import Data", "Export Data", "Backup/Restore"])
    
    with tab1:
        st.subheader("Import Transactions")
        
        st.info("""
            Import transactions from a CSV file. The file should include these columns:
            - date (YYYY-MM-DD)
            - description
            - amount
            - category
            - type (Income/Expense)
            Optional columns: account, recurring, recurring_frequency, recurring_end_date, notes, tags
        """)
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            if st.button("Import Transactions"):
                if import_transactions_from_csv(uploaded_file, user_id):
                    st.rerun()
    
    with tab2:
        st.subheader("Export Transactions")
        
        period = st.selectbox(
            "Select Period",
            ["This Month", "Last Month", "This Year", "Last Year", "Custom", "All"],
            index=0,
            key="export_period"
        )
        
        if period == "All":
            date_range = (None, None)
        else:
            date_range = get_date_range(period)
        
        export_format = st.radio(
            "Export Format",
            ["CSV", "Excel"],
            horizontal=True
        )
        
        if st.button("Generate Export"):
            if export_format == "CSV":
                csv_data = export_transactions_to_csv(date_range, user_id)
                if csv_data:
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="transactions_export.csv",
                        mime="text/csv"
                    )
            else:
                excel_data = export_transactions_to_excel(date_range, user_id)
                if excel_data:
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name="transactions_export.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    
    with tab3:
        st.subheader("Backup and Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Backup Database")
            st.info("Create a backup of your entire finance database")
            if st.button("Create Backup"):
                backup_data = backup_database()
                if backup_data:
                    st.download_button(
                        label="Download Backup",
                        data=backup_data,
                        file_name="finance_backup.db",
                        mime="application/octet-stream"
                    )
        
        with col2:
            st.subheader("Restore Database")
            st.warning("This will overwrite your current database!")
            restore_file = st.file_uploader("Choose a backup file", type="db")
            if restore_file and st.button("Restore Database"):
                if restore_database(restore_file):
                    st.rerun()

# ========== Authentication Pages ==========
def login_page():
    """Display login form"""
    st.title("🔐 Finance Tracker Login")
    
    with st.form(key='login_form'):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user_id
                    st.session_state['username'] = username
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    st.markdown("---")
    st.write("Don't have an account?")
    if st.button("Register New Account"):
        st.session_state['show_register'] = True
        st.rerun()

def register_page():
    """Display registration form"""
    st.title("📝 Register New Account")
    
    with st.form(key='register_form'):
        username = st.text_input("Username", key="register_username")
        email = st.text_input("Email (optional)", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if not username or not password:
                st.error("Username and password are required")
            elif password != confirm_password:
                st.error("Passwords do not match!")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            elif len(username) < 3:
                st.error("Username must be at least 3 characters long")
            else:
                if create_user(username, password, email):
                    st.success("Registration successful! Please login.")
                    st.session_state['show_register'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Registration failed. Username may already exist.")
    
    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state['show_register'] = False
        st.rerun()

# ========== Main App ==========
def main_app():
    """Main application after authentication"""
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    with st.sidebar:
        st.title(f"💰 Finance Tracker Pro+")
        st.markdown(f"Welcome, **{username}**!")
        st.markdown("---")
        
        with st.expander("👤 Profile Settings"):
            if st.button("Logout"):
                st.session_state['authenticated'] = False
                st.session_state['user_id'] = None
                st.session_state['username'] = None
                st.rerun()
            
            profile_pic = st.file_uploader("Upload Profile Picture", type=['jpg', 'png', 'jpeg'])
            if profile_pic:
                try:
                    image = Image.open(profile_pic)
                    st.image(image, width=100)
                    st.success("Profile picture updated!")
                except Exception as e:
                    st.error(f"Error processing image: {e}")
            
            st.subheader("Preferences")
            currency_pref = st.selectbox(
                "Default Currency",
                ["IDR", "USD", "EUR", "GBP", "SGD", "AUD", "JPY"],
                key="currency_pref"
            )
            
            if st.button("Save Preferences"):
                preferences = {
                    'currency': currency_pref,
                    'theme': 'light'
                }
                if update_user_preferences(user_id, preferences):
                    st.success("Preferences saved!")
        
        st.markdown("---")
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "Transactions", "Budgets", "Savings Goals", "Accounts", "Investments", "Reports", "Data Management"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.header("Quick Actions")
        
        with st.form(key='quick_transaction_form'):
            trans_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
            quick_amount = st.number_input("Amount (Rp)", min_value=0.01, step=0.01, value=0.01)  # Changed step to float

            # Limited categories as requested
            if trans_type == "Income":
                category_options = ["Salary"]
            else:
                category_options = [
                    "Bills & Utilities",
                    "Shopping",
                    "Education",
                    "Healthcare",
                    "Entertainment",
                    "Transportation"
                ]
            
            quick_category = st.selectbox(
                "Category",
                options=category_options,
                index=0
            )
            
            accounts = get_accounts(user_id)
            quick_account = st.selectbox(
                "Account",
                options=accounts['name'].tolist() if not accounts.empty else ["Cash"],
                index=0
            )
            quick_desc = st.text_input("Description", placeholder="Brief description")
            
            submitted = st.form_submit_button("💾 Add Transaction")
            if submitted:
                if quick_amount > 0:
                    if add_transaction(
                        datetime.today().strftime('%Y-%m-%d'),
                        quick_desc or f"{quick_category} {trans_type}",
                        quick_amount,
                        quick_category,
                        trans_type,
                        quick_account,
                        False,
                        None,
                        None,
                        None,
                        None,
                        None,
                        user_id
                    ):
                        st.rerun()
                else:
                    st.error("Amount must be greater than 0")
    
    if page == "Dashboard":
        dashboard_page(user_id)
    elif page == "Transactions":
        transactions_page(user_id)
    elif page == "Budgets":
        budgets_page(user_id)
    elif page == "Savings Goals":
        savings_goals_page(user_id)
    elif page == "Accounts":
        accounts_page(user_id)
    elif page == "Investments":
        investments_page(user_id)
    elif page == "Reports":
        reports_page(user_id)
    elif page == "Data Management":
        data_management_page(user_id)

# ========== Initialize Databases ==========
initialize_auth_db()
init_db()
migrate_database()

# ========== App Initialization ==========
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['show_register'] = False

if not st.session_state['authenticated']:
    if st.session_state.get('show_register', False):
        register_page()
    else:
        login_page()
else:
    main_app()

# ========== Footer ==========
st.markdown("""
    <div class="footer">
        <p>💰 <strong>Advanced Finance Tracker Pro+</strong> • v3.0 • Built with Streamlit</p>
        <p>For personal use only • All data remains on your device</p>
    </div>
""", unsafe_allow_html=True)