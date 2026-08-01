import sqlite3
from datetime import datetime

DB_PATH = "prices.db"

def init_db():
    """Створює таблицю для збереження історії цін, якщо її немає"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            shop TEXT,
            name TEXT,
            price REAL,
            is_promo INTEGER,
            url TEXT,
            scraped_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_products_to_db(query: str, products: list[dict]):
    """Зберігає знайдені товари в базу даних"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for p in products:
        cursor.execute("""
            INSERT INTO scraped_prices (query, shop, name, price, is_promo, url, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            query,
            p.get("shop", "Невідомо"),
            p.get("name"),
            p.get("price"),
            1 if p.get("is_promo") else 0,
            p.get("product_url") or p.get("url"),
            now
        ))
    conn.commit()
    conn.close()