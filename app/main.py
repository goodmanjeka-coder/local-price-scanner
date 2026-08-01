import concurrent.futures
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from parsers.eva_parser import parse_eva_soap
from parsers.kopiyochka_parser import parse_kopiyochka
from parsers.aurora_parser import parse_aurora
from app.ai_search import ai_filter_top_10
from app.database import init_db, save_products_to_db, DB_PATH

app = FastAPI(title="Smart Price Scanner 2026")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
def serve_frontend():
    return FileResponse("static/index.html")

@app.on_event("startup")
def startup_event():
    init_db()
    print("\n=== Базу даних SQLite успішно ініціалізовано! ===")

def get_cached_products(query: str, max_age_minutes: int = 30) -> list[dict]:
    """Шукає свіжі результати (не старші за max_age_minutes) в базі даних"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Отримуємо результати у вигляді словників
    cursor = conn.cursor()
    
    # Визначаємо часовий ліміт для "свіжості" даних
    time_limit = (datetime.now() - timedelta(minutes=max_age_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT shop, name, price, is_promo, url as product_url 
        FROM scraped_prices 
        WHERE LOWER(query) = LOWER(?) AND scraped_at >= ?
    """, (query.strip(), time_limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/")
def read_root():
    return {"status": "online", "message": "Мультисканер цін готовий!"}

@app.get("/search")
def search_products(query: str = Query(..., description="Що шукаємо в мережах?")):
    query_clean = query.strip()
    print(f"\n⚡ Отримано запит на пошук: '{query_clean}'")
    
    # КРОК 1: Перевіряємо КЕШ в базі даних (актуальність 30 хвилин)
    cached_products = get_cached_products(query_clean, max_age_minutes=30)
    
    if cached_products:
        print(f"🎯 Знайдено свіжі кешовані дані в базі prices.db ({len(cached_products)} шт). Скрапінг скасовано!")
        all_scraped_products = cached_products
        
        # Підраховуємо статистику з кешу для інтерфейсу
        by_shop = {
            "eva": sum(1 for p in all_scraped_products if p.get("shop") == "Єва"),
            "kopiyochka": sum(1 for p in all_scraped_products if p.get("shop") == "Копійочка"),
            "aurora": sum(1 for p in all_scraped_products if p.get("shop") == "Аврора")
        }
    else:
        # КРОК 2: Якщо кешу немає, запускаємо швидкі паралельні парсери
        print("🔍 Кешу не знайдено. Запускаємо паралельні парсери...")
        all_scraped_products = []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # future_eva = executor.submit(parse_eva_soap, query_clean)
            future_kopiyochka = executor.submit(parse_kopiyochka, query_clean)
            future_aurora = executor.submit(parse_aurora, query_clean)
            
          
            eva_results = []
                
            try:
                kopiyochka_results = future_kopiyochka.result() or []
            except Exception as e:
                print(f"[Помилка Копійочки] {e}")
                kopiyochka_results = []
                
            try:
                aurora_results = future_aurora.result() or []
            except Exception as e:
                print(f"[Помилка Аврори] {e}")
                aurora_results = []

            for r in eva_results: r["shop"] = "Єва"
            for r in kopiyochka_results: r["shop"] = "Копійочка"
            for r in aurora_results: r["shop"] = "Аврора"
            
            all_scraped_products = eva_results + kopiyochka_results + aurora_results
            
            by_shop = {
                "eva": len(eva_results),
                "kopiyochka": len(kopiyochka_results),
                "aurora": len(aurora_results)
            }

        if all_scraped_products:
            try:
                save_products_to_db(query_clean, all_scraped_products)
                print(f"💾 Результати збережено в локальну базу для швидкого кешування.")
            except Exception as e:
                print(f"Помилка збереження в БД: {e}")

    if not all_scraped_products:
        return {
            "search_query": query_clean,
            "message": "Нічого не знайдено.",
            "results": []
        }

    # КРОК 3: Обробка результатів через Gemini
    print("Передаємо список до Gemini...")
    try:
        filtered_results = ai_filter_top_10(query_clean, all_scraped_products)
        ai_status = "success"
    except Exception as e:
        print(f"\n[Fallback] Помилка роботи ШІ: {e}")
        ai_status = "fallback_by_price"
        matching_products = [p for p in all_scraped_products if query_clean.lower() in p.get("name", "").lower()]
        fallback_source = matching_products if matching_products else all_scraped_products
        filtered_results = sorted(fallback_source, key=lambda x: x.get("price", 999))[:10]

    return {
        "search_query": query_clean,
        "total_scraped": len(all_scraped_products),
        "by_shop": by_shop,
        "best_deals": filtered_results,
        "ai_status": ai_status
    }