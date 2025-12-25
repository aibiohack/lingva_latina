import os, json, random, requests, sys
from datetime import datetime, timedelta

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_review_block(history, days_ago, label, current_run_index):
    """
    Берет слова только из конкретного запуска (шага) в прошлом.
    """
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Фильтруем историю: находим все записи за нужный день
    past_entries = [e for e in history if e['date'] == target_date and 'words' in e]
    
    # Если за тот день записей меньше, чем номер текущего шага, берем по кругу (остаток от деления)
    if not past_entries: return ""
    
    entry_index = current_run_index % len(past_entries)
    target_entry = past_entries[entry_index]
    
    review_items = target_entry['words']
    
    text = f"⏳ <b>{label} (шаг {entry_index + 1}):</b>\n"
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
    
    # Определяем номер текущего запуска за сегодня
    # Считаем, сколько записей 'words' уже было создано сегодня
    today_entries_count = len([e for e in history if e['date'] == today_str])
    current_run_index = today_entries_count 

    # --- 1. ЛОГИКА ИСКЛЮЧЕНИЯ ПОВТОРОВ (для НОВЫХ слов) ---
    used_latin_words = set()
    for entry in history:
        if 'words' in entry:
            for w in entry['words']:
                used_latin_words.add(w['latin'])

    available_words = [w for w in data['words'] if w['latin'] not in used_latin_words]
    if len(available_words) < 3:
        available_words = data['words']

    # --- 2. СОБИРАЕМ ПОВТОРЫ С ШАГОМ ---
    # Передаем current_run_index, чтобы бот выбрал только одну порцию слов из прошлого
    review_yesterday = get_review_block(history, 1, "Вчерашний повтор", current_run_index)
    review_3days = get_review_block(history, 3, "Повтор за 3 дня", current_run_index)
    
    # --- 3. ВЫБИРАЕМ НОВЫЕ СЛОВА ---
    new_words = random.sample(available_words, k=3)
    
    # --- 4. ФОРМИРУЕМ СООБЩЕНИЕ ---
    full_message = ""
    
    if review_yesterday or review_3days:
        full_message += "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n\n" + review_yesterday + review_3days + "— — — — — — — —\n\n"

    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # --- 5. СОХРАНЯЕМ В ИСТОРИЮ ---
    history.append({
        "date": today_str,
        "words": new_words
    })
    
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-200:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
