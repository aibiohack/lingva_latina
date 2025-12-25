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

    # --- ШАГ 1: СОБИРАЕМ "БУФЕР ТИШИНЫ" ---
    # Смотрим последние 3 записи в истории, чтобы не брать оттуда слова для повтора
    silence_buffer = set()
    for entry in history[-3:]:
        if 'words' in entry:
            for w in entry['words']: silence_buffer.add(w['latin'])
        if 'reviewed_today' in entry:
            for lat in entry['reviewed_today']: silence_buffer.add(lat)

    # --- ШАГ 2: СОБИРАЕМ ПУЛ ДЛЯ ПОВТОРА ИЗ ВСЕЙ ИСТОРИИ ---
    review_pool = []
    seen_in_pool = set()

    for entry in history:
        if 'words' in entry:
            for w in entry['words']:
                # Берем слово, если его нет в буфере тишины и мы его еще не добавили в пул
                if w['latin'] not in silence_buffer and w['latin'] not in seen_in_pool:
                    review_pool.append(w)
                    seen_in_pool.add(w['latin'])

    # --- ШАГ 3: ВЫБИРАЕМ СЛОВА ДЛЯ ПОВТОРА ---
    current_review = []
    if len(review_pool) >= 3:
        current_review = random.sample(review_pool, 3)
    elif len(review_pool) > 0:
        current_review = review_pool # Берем сколько есть, если база еще маленькая
    else:
        # Если совсем пусто (самый первый запуск), берем случайные из базы данных
        current_review = random.sample(data['words'], 3)

    # --- ШАГ 4: ВЫБИРАЕМ 3 НОВЫХ СЛОВА ---
    # Исключаем вообще всё, что когда-либо было в истории как "новое"
    all_time_new_seen = set()
    for entry in history:
        if 'words' in entry:
            for w in entry['words']: all_time_new_seen.add(w['latin'])

    available_new = [w for w in data['words'] if w['latin'] not in all_time_new_seen]
    if len(available_new) < 3: available_new = data['words']
    
    new_words = random.sample(available_new, k=3)

    # --- ШАГ 5: ФОРМИРУЕМ СООБЩЕНИЕ ---
    # Блок "Вспомнить" теперь ВСЕГДА имеет контент
    full_message = "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n"
    full_message += "\n".join([f"• {w['ru']} — <tg-spoiler>{w['latin']}</tg-spoiler>" for w in current_review])
    full_message += "\n\n— — — — — — — —\n\n"

    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # --- ШАГ 6: СОХРАНЕНИЕ ---
    history.append({
        "date": today_str,
        "words": new_words,
        "reviewed_today": [w['latin'] for w in current_review]
    })
    
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-500:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
