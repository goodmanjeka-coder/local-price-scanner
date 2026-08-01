import requests

KOPIYOCHKA_AJAX_URL = "https://www.kopiyochka.ua/user-pannel/admin-ajax.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.kopiyochka.ua/catalog/",
    "Origin": "https://www.kopiyochka.ua",
}

def parse_kopiyochka(search_query: str) -> list[dict]:
    """Шукає товари на Копійочці за текстовим запитом через AJAX (реальні ціни)."""
    payload = {
        "action": "get_catalog_products",
        "place_id": "",
        "category_term_id": "",
        "offset": "0",
        "search_query": search_query,
        "sort_by": "popularity",
    }

    files = {key: (None, value) for key, value in payload.items()}

    try:
        response = requests.post(KOPIYOCHKA_AJAX_URL, files=files, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else data
        print(f"[Копійочка DEBUG] total: {data.get('total') if isinstance(data, dict) else '?'}")
    except (requests.RequestException, ValueError) as e:
        print(f"[Копійочка] Помилка: {e}")
        return []

    products = []
    for item in items:
        if not isinstance(item, dict):
            continue

        base_price = item.get("base_unit_price")
        promo_price = item.get("promo_unit_price")
        price = promo_price if promo_price and promo_price != "0.00" else base_price

        if not price:
            continue

        products.append({
            "name": item.get("post_title"),
            "price": float(price),
            "is_promo": bool(promo_price and promo_price != "0.00"),
            "product_url": item.get("url"),
        })

    print(f"[Копійочка] Знайдено товарів з реальними цінами: {len(products)}")
    return products