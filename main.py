import os, json, random, requests, sys
from datetime import datetime, timedelta

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_run_slot():
    """Определяет номер слота (0, 1, 2, 3) в зависимости от текущего часа (UTC)"""
    hour = datetime.utcnow().hour
    if hour < 10: return 0   # Утро
    if hour < 14: return 1   # День
    if hour < 18: return 2   # Вечер
    return 3                 # Ночь

def get_review_block(history, days_ago, label, slot):
    """Берет слова из конкретного слота прошлого дня"""
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Ищем записи за целевой день
    past_entries = [e for e in history if e['date'] == target_date and 'words' in e]
    
    if not past_entries: return ""
    
    # Берем запись, соответствующую текущему временному слоту
    # Если записей меньше 4, используем остаток от деления, чтобы не выйти за пределы списка
    entry_index = slot % len(past_entries)
    target_entry = past_entries[entry_index]
    
    review_items = target_entry['words']
    
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
    
    # Определяем текущий временной слот (0, 1, 2 или 3)
    current_slot = get_run_slot()

    # --- 1. ИСКЛЮЧЕНИЕ ПОВТОРОВ ДЛЯ НОВЫХ СЛОВ ---
    # Собираем слова, которые были в последних 50 записях
    used_latin_words = set()
    for entry in history[-50:]:
        if 'words' in entry:
            for w in entry['words']:
                used_latin_words.add(w['latin'])

    available_words = [w for w in data['words'] if w['latin'] not in used_latin_words]
    if len(available_words) < 3:
        available_words = data['words']

    # --- 2. ПОВТОРЫ С ПРИВЯЗКОЙ К СЛОТУ ---
    review_yesterday = get_review_block(history, 1, "Вчерашний повтор", current_slot)
    review_3days = get_review_block(history, 3, "Повтор за 3 дня назад", current_slot)
    
    # --- 3. НОВЫЕ СЛОВА ---
    new_words = random.sample(available_words, k=3)
    
    # --- 4. СООБЩЕНИЕ ---
    full_message = ""
    
    if review_yesterday or review_3days:
        # Указываем время слота для визуальной проверки
        slot_names = ["Утренний", "Дневной", "Вечерний", "Ночной"]
        full_message += f"🧠 <b>ВРЕМЯ ВСПОМНИТЬ ({slot_names[current_slot]}):</b>\n\n"
        full_message += review_yesterday + review_3days + "— — — — — — — —\n\n"

    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # --- 5. СОХРАНЕНИЕ ---
    history.append({
        "date": today_str,
        "words": new_words,
        "slot": current_slot
    })
    
    # Ограничиваем историю 200 записями
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-200:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
    
