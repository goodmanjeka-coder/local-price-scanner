import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

AURORA_BASE_URL = "https://avrora.ua/"


def _get_search_hash(session: requests.Session) -> str | None:
    """Заходить на головну сторінку і дістає звідти актуальний security_hash
    з прихованого поля форми пошуку (потрібен для наступного запиту пошуку)."""
    try:
        response = session.get(AURORA_BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Аврора] Помилка запиту головної сторінки: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    hash_input = soup.select_one('input[name="security_hash"]')

    if not hash_input or not hash_input.get("value"):
        print("[Аврора] Не знайдено security_hash на головній сторінці")
        return None

    return hash_input["value"]


def parse_aurora(search_query: str) -> list[dict]:
    """Шукає товари на Аврорі: спершу отримує security_hash, потім робить пошук."""
    session = requests.Session()

    security_hash = _get_search_hash(session)
    if not security_hash:
        return []

    search_url = "https://avrora.ua/index.php"
    params = {
        "dispatch": "products.search",
        "q": search_query,
        "subcats": "Y",
        "status": "A",
        "pshort": "Y",
        "pfull": "Y",
        "pname": "Y",
        "pkeywords": "Y",
        "pcode_from_q": "Y",
        "search_performed": "Y",
        "security_hash": security_hash,
    }

    try:
        response = session.get(search_url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Аврора] Помилка запиту пошуку: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    product_cards = soup.select("div.ty-grid-list__item")

    products = []
    for card in product_cards:
        name_tag = card.select_one("a.product-title")
        price_tag = card.select_one(".ty-price-num")

        if not name_tag or not price_tag:
            continue

        try:
            price = float(price_tag.get_text(strip=True).replace(" ", "").replace(",", "."))
        except ValueError:
            continue

        products.append({
            "name": name_tag.get_text(strip=True),
            "price": price,
            "is_promo": False,
            "product_url": name_tag.get("href", ""),
        })

    print(f"[Аврора] Знайдено товарів з реальними цінами: {len(products)}")
    return products