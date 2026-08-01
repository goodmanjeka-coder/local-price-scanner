import time
import urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def parse_eva_soap(search_query: str):
    # Очищаємо запит
    words = search_query.strip().split()
    base_query = words[0] if words else search_query
    
    encoded_query = urllib.parse.quote(base_query)
    url = f"https://eva.ua/ua/search/?q={encoded_query}"
    products_list = []
    
    print(f"[Єва] Швидкий запуск для: {url}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="uk-UA"
            )
            page = context.new_page()
            
            # 🔥 ТРЮК: Блокуємо завантаження картинок, шрифтів та стилів для супер-швидкості!
            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] else route.continue_())
            
            # Переходимо на сайт
            page.goto(url, timeout=30000, wait_until="commit") # wait_until="commit" значно швидший за "load"
            
            # Чекаємо появи хоча б одного товару (максимум 4 секунди), замість фіксованих time.sleep(5)
            try:
                page.wait_for_selector(".product-card, a[href*='/pr']", timeout=4000)
            except Exception:
                pass # якщо не з'явився, спробуємо розпарсити те, що є
            
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, "html.parser")
        
        seen_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/pr" in href and href not in seen_urls:
                seen_urls.add(href)
                title = a.text.strip()
                if len(title) > 12:
                    price = 45.0
                    parent = a.find_parent()
                    if parent:
                        price_tag = parent.select_one("[class*='price'], .price, .product-card__price")
                        if price_tag:
                            try:
                                price_text = "".join(c for c in price_tag.text if c.isdigit() or c in ".,")
                                price = float(price_text.replace(",", "."))
                            except ValueError:
                                pass

                    products_list.append({
                        "name": title,
                        "price": price,
                        "is_promo": False,
                        "product_url": "https://eva.ua" + href if not href.startswith("http") else href,
                        "shop": "Єва"
                    })
        
        print(f"[Єва] Швидко знайдено потенційних товарів: {len(products_list)}")
        return products_list

    except Exception as e:
        print(f"[Єва] Помилка: {e}")
        return []