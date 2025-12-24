import os, json, random, requests, sys
from datetime import datetime, timedelta

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_review_block(history, days_ago, label):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    review_items = []
    for entry in history:
        # Собираем только слова (тип 'words' или из утреннего запуска)
        if entry['date'] == target_date and 'words' in entry:
            review_items.extend(entry['words'])
    
    if not review_items: return ""
    
    text = f"⏳ <b>{label}:</b>\n"
    for w in review_items:
        text += f"• {w['ru']} — <tg-spoiler>{w['latin']}</tg-spoiler>\n"
    return text + "\n"

def main():
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    history = []
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)

    today_str = datetime.now().strftime("%Y-%m-%d")
    mode = sys.argv[1] if len(sys.argv) > 1 else "words"
    
    # 1. СОБИРАЕМ ПОВТОРЫ (Вчера и 3 дня назад)
    review_yesterday = get_review_block(history, 1, "Вчерашние слова")
    review_3days = get_review_block(history, 3, "Повтор за 3 дня назад")
    
    # 2. ВЫБИРАЕМ НОВЫЕ СЛОВА (Всегда 3 штуки)
    new_words = random.sample(data['words'], k=3)
    
    # 3. ФОРМИРУЕМ СООБЩЕНИЕ
    full_message = ""
    
    # Добавляем повторы в начало, если они есть
    if review_yesterday or review_3days:
        full_message += "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n\n" + review_yesterday + review_3days + "— — — — — — — —\n\n"

    # Добавляем цитату ТОЛЬКО УТРОМ
    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    # Добавляем новые слова
    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # 4. СОХРАНЯЕМ В ИСТОРИЮ
    # Сохраняем только слова для будущего повтора
    history.append({
        "date": today_str,
        "words": new_words
    })
    
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-100:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
