import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "fishing_gear.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create gear table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gear (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price TEXT,
            characteristics TEXT,
            verified INTEGER DEFAULT 0
        )
    """)

    # Add price column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE gear ADD COLUMN price TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            rating REAL DEFAULT 0.0,
            verified INTEGER DEFAULT 0,
            last_checked TEXT,
            domain_age_days INTEGER DEFAULT 0,
            has_contact_info INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gear_id INTEGER,
            shop_id INTEGER,
            price REAL,
            url TEXT,
            date TEXT,
            in_stock INTEGER DEFAULT 1,
            FOREIGN KEY (gear_id) REFERENCES gear(id),
            FOREIGN KEY (shop_id) REFERENCES shops(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gear_id INTEGER,
            title TEXT,
            price REAL,
            condition TEXT,
            source TEXT,
            url TEXT,
            location TEXT,
            seller_rating REAL DEFAULT 0.0,
            date TEXT,
            FOREIGN KEY (gear_id) REFERENCES gear(id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM gear")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.commit()
    conn.close()


def seed_data(conn: sqlite3.Connection):
    categories = {
        "Удочки": [
            {"name": "Спиннинг Fox Rage", "description": "Универсальный спиннинг для начинающих", "chars": {"длина": "2.1м", "тест": "10-30г", "материал": "углепластик"}},
            {"name": "Маховая удочка Trabucco", "description": "Для ловли на поплавок", "chars": {"длина": "5м", "секции": "5", "материал": "карбон"}},
            {"name": "Фидер Trabucco", "description": "Для дальнего заброса", "chars": {"длина": "3.6м", "тест": "60г", "материал": "композит"}},
        ],
        "Катушки": [
            {"name": "Катушка Shimano Sedona", "description": "Безынерционная, 5 подшипников", "chars": {"размер": "2500", "передаточное": "5.1:1", "лесоемкость": "150м/0.25мм"}},
            {"name": "Катушка Daiwa Ninja", "description": "Недорогая и надежная", "chars": {"размер": "2000", "передаточное": "5.3:1", "подшипники": "3"}},
        ],
        "Лески": [
            {"name": "Леска PowerPro", "description": "Плетёная, 150м", "chars": {"длина": "150м", "диаметр": "0.14мм", "разрывная": "8кг"}},
            {"name": "Леска Trabucco TForce", "description": "Монофильная", "chars": {"длина": "100м", "диаметр": "0.25мм", "разрывная": "5кг"}},
        ],
        "Крючки": [
            {"name": "Крючки Owner Iseama", "description": "Одинарные, №6", "chars": {"размер": "№6", "количество": "10 шт", "тип": "одинарный"}},
            {"name": "Крючки Mustad Classic", "description": "Двойные, №4", "chars": {"размер": "№4", "количество": "8 шт", "тип": "двойной"}},
        ],
        "Приманки": [
            {"name": "Блесна Mepps Aglia", "description": "Вращающаяся, №2", "chars": {"размер": "№2", "вес": "6г", "цвет": "серебро"}},
            {"name": "Силикон Lucky John", "description": "Твистер, 50мм", "chars": {"длина": "50мм", "количество": "10 шт", "материал": "силикон"}},
            {"name": "Воблер Yo-Zuri", "description": "Кренк, 5см", "chars": {"длина": "5см", "вес": "7г", "заглубление": "1-2м"}},
        ],
    }

    cursor = conn.cursor()
    for category, items in categories.items():
        for item in items:
            cursor.execute(
                "INSERT INTO gear (name, category, description, characteristics) VALUES (?, ?, ?, ?)",
                (item["name"], category, item["description"], json.dumps(item["chars"]))
            )


def get_all_categories() -> list[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM gear ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories


def get_gear_by_category(category: str) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM gear WHERE category = ?", (category,))
    result = cursor.fetchall()
    conn.close()
    return result


def get_gear_by_id(gear_id: int) -> Optional:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gear WHERE id = ?", (gear_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def search_gear(query: str) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, category, price FROM gear WHERE name LIKE ? OR description LIKE ?",
        (f"%{query}%", f"%{query}%")
    )
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_gear() -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, price FROM gear ORDER BY category, name")
    result = cursor.fetchall()
    conn.close()
    return result


def add_shop(name: str, url: str) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO shops (name, url) VALUES (?, ?)", (name, url))
    conn.commit()
    cursor.execute("SELECT id FROM shops WHERE url = ?", (url,))
    shop_id = cursor.fetchone()[0]
    conn.close()
    return shop_id


def update_shop_verification(shop_id: int, data: dict):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE shops SET
            rating = ?,
            verified = ?,
            last_checked = ?,
            domain_age_days = ?,
            has_contact_info = ?,
            review_count = ?
        WHERE id = ?
    """, (
        data.get("rating", 0),
        data.get("verified", 0),
        datetime.now().isoformat(),
        data.get("domain_age_days", 0),
        data.get("has_contact_info", 0),
        data.get("review_count", 0),
        shop_id
    ))
    conn.commit()
    conn.close()


def get_shop_by_url(url: str) -> Optional:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shops WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result


def add_price(gear_id: int, shop_id: int, price: float, url: str, in_stock: bool = True) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prices (gear_id, shop_id, price, url, date, in_stock)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (gear_id, shop_id, price, url, datetime.now().isoformat(), 1 if in_stock else 0))
    conn.commit()
    price_id = cursor.lastrowid
    conn.close()
    return price_id


def get_prices_for_gear(gear_id: int) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, s.name as shop_name, s.rating as shop_rating, s.verified as shop_verified
        FROM prices p
        JOIN shops s ON p.shop_id = s.id
        WHERE p.gear_id = ? AND p.in_stock = 1
        ORDER BY p.price ASC
    """, (gear_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def add_used_item(gear_id: int, title: str, price: float, condition: str,
                  source: str, url: str, location: str, seller_rating: float = 0.0) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO used_items (gear_id, title, price, condition, source, url, location, seller_rating, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (gear_id, title, price, condition, source, url, location, seller_rating, datetime.now().isoformat()))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def get_used_items_for_gear(gear_id: int) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM used_items
        WHERE gear_id = ?
        ORDER BY price ASC
    """, (gear_id,))
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_shops() -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shops ORDER BY rating DESC")
    result = cursor.fetchall()
    conn.close()
    return result


def get_cheapest_price(gear_id: int) -> Optional:
    prices = get_prices_for_gear(gear_id)
    return prices[0] if prices else None


def get_analogues(gear_id: int) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT category FROM gear WHERE id = ?", (gear_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []

    category = row[0]
    cursor.execute("""
        SELECT id, name, description FROM gear
        WHERE category = ? AND id != ?
    """, (category, gear_id))
    result = cursor.fetchall()
    conn.close()
    return result