import sqlite3

def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            balance INT NOT NULL
        )
    ''')
    # FLAW 2 - A04:2025 Cryptographic Failures
    # This flaw is heavily tied to A07:2025 Authentication Failures. This vulnerability allows attacker to brute-force password checks easily because passwords are not hashed.
    # Passwords are not hashed and are stored in plain human readable form when creating a database.
    # See more app.py:25
    users_data = [
        ("admin", "admin123", "admin", 999999),
        ("user1", "password", "user", 1000),
        ("user2", "testi123", "user", 1000)
    ]
    # FLAW 2 FIX:
    # from werkzeug.security import generate_password_hash
    # users_data = [
    #     ("admin", generate_password_hash("admin123"), "admin", 999999),
    #     ("user1", generate_password_hash("password"), "user", 1000),
    #     ("user2", generate_password_hash("testi123"), "user", 1000)
    # ]
    # See more db.py:52
    conn.executemany(
        'INSERT OR IGNORE INTO users (username, password, role, balance) VALUES (?, ?, ?, ?)',
        users_data
    )
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def check_login(username, password):
    user = get_user(username)
    if user and user["password"] == password:
        return user
    # FLAW 2 FIX:
    # from werkzeug.security import check_password_hash
    # if user and check_password_hash(user['password'], password):
    #     return user
    return None

def transfer(user1, user2, amount):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE username = ?', (user1,)).fetchone()
        
    if user_data["balance"] < amount:
        conn.close()
        return False, "Not enough funds", None
        
    conn.execute('UPDATE users SET balance = balance - ? WHERE username = ?', (amount, user1))
    conn.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (amount, user2))
    conn.commit()
    conn.close()
    return True, "Success"
