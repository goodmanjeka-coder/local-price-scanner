import streamlit as st
import requests
import pandas as pd

# Налаштування сторінки
st.set_page_config(
    page_title="Мультисканер цін 2026",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Розумний Мультисканер Цін")
st.markdown("Порівняння цін у реальному часі між мережами **Єва**, **Аврора** та **Копійочка** за підтримки ШІ.")

# Поле введення запиту
query = st.text_input("Що ви хочете знайти?", placeholder="Наприклад: дитяче мило, зубна паста, порошок...")

if st.button("Знайти найкращі ціни", type="primary"):
    if not query.strip():
        st.warning("Будь ласка, введіть пошуковий запит!")
    else:
        with st.spinner(f"Шукаємо '{query}' в усіх магазинах... Це займе кілька секунд 🔎"):
            try:
                # Робимо запит до нашого FastAPI бекенду
                response = requests.get(f"http://127.0.0.1:8000/search?query={query}", timeout=60)
                
                if response.status_code != 200:
                    st.error(f"Помилка сервера бекенду (Код {response.status_code}). Перевірте термінал FastAPI.")
                    st.stop()
                
                data = response.json()
                
                # Перевірка на випадок, якщо бекенд надіслав пусту відповідь або None
                if not data or not isinstance(data, dict):
                    st.error("Отримано некоректну або порожню відповідь від сервера.")
                    st.stop()
                
                # Статистика пошуку
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Знайдено всього", f"{data.get('total_scraped', 0)} шт")
                col2.metric("В мережі Єва", f"{data.get('by_shop', {}).get('eva', 0)} шт")
                col3.metric("В мережі Копійочка", f"{data.get('by_shop', {}).get('kopiyochka', 0)} шт")
                col4.metric("В мережі Аврора", f"{data.get('by_shop', {}).get('aurora', 0)} шт")
                
                st.subheader("🏆 Найкращі пропозиції (відібрано ШІ / відсортовано за ціною)")
                
                best_deals = data.get("best_deals", [])
                
                if not best_deals:
                    st.info("На жаль, за цим запитом нічого не знайдено.")
                else:
                    # Перетворюємо результати в таблицю pandas для зручності
                    formatted_deals = []
                    for item in best_deals:
                        formatted_deals.append({
                            "Магазин": f"🏪 {item.get('shop')}",
                            "Назва товару": item.get("name"),
                            "Ціна (грн)": f"{item.get('price')} грн",
                            "Акція": "🔥 Так" if item.get("is_promo") else "Звичайна ціна",
                            "Посилання": item.get("product_url") or item.get("url")
                        })
                    
                    df = pd.DataFrame(formatted_deals)
                    
                    # Виводимо інтерактивну таблицю з посиланнями
                    st.dataframe(
                        df, 
                        column_config={
                            "Посилання": st.column_config.LinkColumn("Перейти до товару")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Виводимо статус ШІ
                    ai_status = data.get("ai_status")
                    if "success" in str(ai_status):
                        st.success("🤖 Результати успішно відфільтровані та оптимізовані за допомогою Gemini 2.5-flash!")
                    else:
                        st.info("⚡ Результати відсортовані за ціною (резервний режим без ШІ).")
                        
            except requests.exceptions.RequestException as e:
                st.error(f"Не вдалося зв'язатися з сервером FastAPI. Переконайтеся, що uvicorn запущений. Помилка: {e}")

# Корисний підвал
st.markdown("---")
st.caption("Local Price Scanner API v2.0 (2026). Усі права захищені.")