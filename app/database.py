import psycopg2
import psycopg2.extras
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Створює таблицю для збереження історії цін, якщо її немає"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_prices (
            id SERIAL PRIMARY KEY,
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
    cursor.close()
    conn.close()

def save_products_to_db(query: str, products: list[dict]):
    """Зберігає знайдені товари в базу даних"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for p in products:
        cursor.execute("""
            INSERT INTO scraped_prices (query, shop, name, price, is_promo, url, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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
    cursor.close()
    conn.close()