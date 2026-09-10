import os
import sqlite3
import datetime

# MySQL Environment Configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'callshield_db')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))

# SQLite Fallback Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)
SQLITE_DB_PATH = os.path.join(INSTANCE_DIR, 'callshield.db')

DB_MODE = 'UNKNOWN'

def get_mysql_connection(create_db_if_missing=True):
    """Attempts to connect to MySQL database server."""
    try:
        import pymysql
        if create_db_if_missing:
            conn_root = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                port=MYSQL_PORT,
                autocommit=True
            )
            with conn_root.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn_root.close()

        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, 'MYSQL'
    except Exception as e1:
        try:
            import mysql.connector
            if create_db_if_missing:
                conn_root = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    port=MYSQL_PORT
                )
                cursor = conn_root.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`")
                cursor.close()
                conn_root.close()

            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                port=MYSQL_PORT,
                autocommit=True
            )
            return conn, 'MYSQL'
        except Exception as e2:
            return None, str(e1)

def get_db_connection():
    """Get active DB connection (MySQL preferred, SQLite fallback)."""
    global DB_MODE
    conn, mode = get_mysql_connection()
    if conn is not None:
        DB_MODE = 'MYSQL'
        return conn, 'MYSQL'
    
    # SQLite Fallback
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        sqlite_conn.row_factory = sqlite3.Row
        DB_MODE = 'SQLITE'
        return sqlite_conn, 'SQLITE'
    except Exception as e:
        mem_conn = sqlite3.connect(':memory:', check_same_thread=False)
        mem_conn.row_factory = sqlite3.Row
        DB_MODE = 'SQLITE_MEMORY'
        return mem_conn, 'SQLITE_MEMORY'

def init_db():
    """Initializes tables and populates default sample records."""
    conn, mode = get_db_connection()
    if not conn:
        print("[-] Database connection failed.")
        return False

    try:
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS call_reports (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        call_type VARCHAR(50) DEFAULT 'live_call',
                        phone_number VARCHAR(50) DEFAULT '',
                        name VARCHAR(255) NOT NULL,
                        transcript TEXT,
                        scam_type VARCHAR(255),
                        fraud_score INT DEFAULT 0,
                        risk_level VARCHAR(50) DEFAULT 'Low',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        number VARCHAR(50) NOT NULL,
                        category VARCHAR(50) DEFAULT 'Safe',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        sender VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        response TEXT,
                        source VARCHAR(100) DEFAULT 'assistant',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                cursor.execute("SELECT COUNT(*) AS cnt FROM contacts")
                row = cursor.fetchone()
                cnt = row['cnt'] if isinstance(row, dict) else row[0]
                if cnt == 0:
                    cursor.executemany(
                        "INSERT INTO contacts (name, number, category) VALUES (%s, %s, %s)",
                        [
                            ("Mom", "+1 555-0192", "Safe"),
                            ("Bank Customer Service", "+1 800-555-0199", "Verified"),
                            ("Manager John", "+1 555-0143", "Safe"),
                            ("Tech Support Hotline", "+1 555-0188", "Suspicious"),
                            ("Emergency Services", "911", "Emergency")
                        ]
                    )
            conn.close()
            print("[+] MySQL Database & Tables Initialized Successfully.")
        else:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_type TEXT DEFAULT 'live_call',
                    phone_number TEXT DEFAULT '',
                    name TEXT NOT NULL,
                    transcript TEXT,
                    scam_type TEXT,
                    fraud_score INTEGER DEFAULT 0,
                    risk_level TEXT DEFAULT 'Low',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    number TEXT NOT NULL,
                    category TEXT DEFAULT 'Safe',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT,
                    source TEXT DEFAULT 'assistant',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("SELECT COUNT(*) FROM contacts")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO contacts (name, number, category) VALUES (?, ?, ?)",
                    [
                        ("Mom", "+1 555-0192", "Safe"),
                        ("Bank Customer Service", "+1 800-555-0199", "Verified"),
                        ("Manager John", "+1 555-0143", "Safe"),
                        ("Tech Support Hotline", "+1 555-0188", "Suspicious"),
                        ("Emergency Services", "911", "Emergency")
                    ]
                )
            conn.commit()
            conn.close()
            print(f"[+] SQLite Database ({mode}) Initialized Successfully.")
        return True
    except Exception as e:
        print(f"[!] Error initializing database: {e}")
        return False

def save_call_report(name, transcript, scam_type, fraud_score=0, risk_level='Low', phone_number='', call_type='live_call'):
    """Save call recording analysis report into database."""
    conn, mode = get_db_connection()
    if not conn:
        return False

    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO call_reports (name, transcript, scam_type, fraud_score, risk_level, phone_number, call_type, timestamp)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (name, transcript, scam_type, fraud_score, risk_level, phone_number, call_type, now)
                )
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO call_reports (name, transcript, scam_type, fraud_score, risk_level, phone_number, call_type, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, transcript, scam_type, fraud_score, risk_level, phone_number, call_type, now)
            )
            conn.commit()
            conn.close()
        return True
    except Exception as e:
        print(f"[!] Error saving call report: {e}")
        return False

def get_call_reports():
    """Retrieve all recorded call reports."""
    conn, mode = get_db_connection()
    if not conn:
        return []

    reports = []
    try:
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM call_reports ORDER BY id DESC")
                rows = cursor.fetchall()
                for r in rows:
                    reports.append({
                        "id": r['id'],
                        "name": r['name'],
                        "transcript": r['transcript'],
                        "scam_type": r['scam_type'],
                        "fraud_score": r['fraud_score'],
                        "risk_level": r['risk_level'],
                        "phone_number": r['phone_number'],
                        "date": str(r['timestamp'])
                    })
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM call_reports ORDER BY id DESC")
            rows = cursor.fetchall()
            for r in rows:
                reports.append({
                    "id": r['id'],
                    "name": r['name'],
                    "transcript": r['transcript'],
                    "scam_type": r['scam_type'],
                    "fraud_score": r['fraud_score'],
                    "risk_level": r['risk_level'],
                    "phone_number": r['phone_number'],
                    "date": str(r['timestamp'])
                })
            conn.close()
    except Exception as e:
        print(f"[!] Error fetching call reports: {e}")
    return reports

def save_contact(name, number, category='Safe'):
    """Insert or update a contact in the database."""
    conn, mode = get_db_connection()
    if not conn:
        return False
    try:
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO contacts (name, number, category) VALUES (%s, %s, %s)", (name, number, category))
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contacts (name, number, category) VALUES (?, ?, ?)", (name, number, category))
            conn.commit()
            conn.close()
        return True
    except Exception as e:
        print(f"[!] Error saving contact: {e}")
        return False

def get_contacts():
    """Retrieve all contacts from database."""
    conn, mode = get_db_connection()
    if not conn:
        return []
    contacts = []
    try:
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM contacts ORDER BY name ASC")
                rows = cursor.fetchall()
                for r in rows:
                    contacts.append({"id": r['id'], "name": r['name'], "number": r['number'], "category": r['category']})
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts ORDER BY name ASC")
            rows = cursor.fetchall()
            for r in rows:
                contacts.append({"id": r['id'], "name": r['name'], "number": r['number'], "category": r['category']})
            conn.close()
    except Exception as e:
        print(f"[!] Error fetching contacts: {e}")
    return contacts

def save_chat_log(sender, message, response='', source='assistant'):
    """Save user-bot chatbot interaction log into database."""
    conn, mode = get_db_connection()
    if not conn:
        return False
    try:
        if mode == 'MYSQL':
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chat_logs (sender, message, response, source) VALUES (%s, %s, %s, %s)",
                    (sender, message, response, source)
                )
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_logs (sender, message, response, source) VALUES (?, ?, ?, ?)",
                (sender, message, response, source)
            )
            conn.commit()
            conn.close()
        return True
    except Exception as e:
        print(f"[!] Error saving chat log: {e}")
        return False
