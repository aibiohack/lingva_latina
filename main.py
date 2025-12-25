import os, json, random, requests, sys
from datetime import datetime, timedelta

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def main():
    # 1. Загрузка данных
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    history = []
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)

    today_str = datetime.now().strftime("%Y-%m-%d")
    mode = sys.argv[1] if len(sys.argv) > 1 else "words"
    
    # --- ЛОГИКА СБОРА СЛОВ ДЛЯ ПОВТОРА (АРХИВ ЗА 7 ДНЕЙ) ---
    all_seen_words = []
    today_seen_latin = set()
    
    # Собираем слова за последние 7 дней
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    for entry in history:
        entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
        if 'words' in entry:
            if entry['date'] == today_str:
                # Запоминаем, что уже видели сегодня, чтобы НЕ повторять это в блоке "Вспомнить"
                for w in entry['words']:
                    today_seen_latin.add(w['latin'])
            elif entry_date > seven_days_ago:
                # Добавляем слова из прошлого в пул для повторения
                all_seen_words.extend(entry['words'])

    # Убираем дубликаты из пула повторов и исключаем то, что было сегодня
    review_pool = []
    seen_in_pool = set()
    for w in all_seen_words:
        if w['latin'] not in today_seen_latin and w['latin'] not in seen_in_pool:
            review_pool.append(w)
            seen_in_pool.add(w['latin'])

    # --- 1. ВЫБИРАЕМ СЛОВА ДЛЯ ПОВТОРА ---
    # Берем 3 случайных слова из тех, что учили за неделю (но не сегодня)
    review_content = ""
    if review_pool:
        # Чтобы слова менялись в каждом сообщении, используем random.sample
        review_samples = random.sample(review_pool, min(3, len(review_pool)))
        review_content = "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n\n"
        for w in review_samples:
            review_content += f"• {w['ru']} — <tg-spoiler>{w['latin']}</tg-spoiler>\n"
        review_content += "\n— — — — — — — —\n\n"

    # --- 2. ИСКЛЮЧАЕМ ПОВТОРЫ ДЛЯ НОВЫХ СЛОВ ---
    # Собираем абсолютно все слова из истории, чтобы НОВЫЕ были реально новыми
    long_term_seen = set()
    for entry in history:
        if 'words' in entry:
            for w in entry['words']:
                long_term_seen.add(w['latin'])

    available_new = [w for w in data['words'] if w['latin'] not in long_term_seen]
    if len(available_new) < 3: available_new = data['words']

    # Выбираем 3 новых слова
    new_words = random.sample(available_new, k=3)
    
    # --- 3. ФОРМИРУЕМ ИТОГОВОЕ СООБЩЕНИЕ ---
    full_message = review_content

    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # --- 4. СОХРАНЯЕМ В ИСТОРИЮ ---
    history.append({
        "date": today_str,
        "words": new_words
    })
    
    # Держим историю подлиннее (300 записей), чтобы база была чище
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-300:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
