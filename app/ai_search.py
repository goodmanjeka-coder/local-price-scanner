import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

import os
from dotenv import load_dotenv

load_dotenv()  # зчитує .env файл у змінні середовища

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY не знайдено в .env файлі")

# Ініціалізуємо клієнт з правильним шлюзом v1
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1'}
)

def ai_filter_top_10(query: str, products: list) -> list:
    if not products:
        return []
        
    # Формуємо текстовий список товарів для ШІ
    items_text = ""
    for idx, p in enumerate(products):
        items_text += f"{idx}. {p['name']}\n"
        
    prompt = f"""
    Тобі дано список товарів:
    {items_text}
    
    Користувач шукає: "{query}".
    Викресли з цього списку все, що взагалі НЕ стосується запиту "{query}".
    Поверни відповідь ТІЛЬКИ як список індексів через кому всередині квадратних дужок.
    Наприклад, якщо підходять тільки товари 4 та 5, напиши: [4, 5]
    Нічого більше не пиши, жодних слів чи пояснень. Тільки масив, як [0, 1].
    """
    
    try:
        # Викликаємо актуальну модель gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        text_response = response.text.strip()
        
        # Очищаємо від можливих markdown-тегів, які ШІ іноді додає
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        
        # Перетворюємо рядок на список індексів в Python
        best_indices = json.loads(text_response)
        print(f"\n--- УСПІХ! ШІ вибрав індекси товарів: {best_indices} ---\n")
        
        return [products[idx] for idx in best_indices if idx < len(products)]
        
    except Exception as e:
        print(f"\n--- ПОМИЛКА РОБОТИ ШІ: {e} ---\n")
        return products[:2]