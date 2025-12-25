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
    # 1. Загрузка базы
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    history = []
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)

    today_str = datetime.now().strftime("%Y-%m-%d")
    mode = sys.argv[1] if len(sys.argv) > 1 else "words"

    # --- ШАГ 1: СОБИРАЕМ ВСЁ, ЧТО БЫЛО СЕГОДНЯ ---
    # (Чтобы не повторять это в блоке "Вспомнить")
    today_latin = set()
    for entry in history:
        if entry['date'] == today_str:
            if 'words' in entry:
                for w in entry['words']: today_latin.add(w['latin'])
            if 'reviewed_today' in entry:
                for lat in entry['reviewed_today']: today_latin.add(lat)

    # --- ШАГ 2: СОБИРАЕМ ПУЛ ДЛЯ ПОВТОРА ЗА 10 ДНЕЙ ---
    review_pool = []
    seen_in_pool = set()
    ten_days_ago = datetime.now() - timedelta(days=10)

    for entry in history:
        entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
        if ten_days_ago <= entry_date < datetime.now().replace(hour=0, minute=0, second=0):
            if 'words' in entry:
                for w in entry['words']:
                    if w['latin'] not in today_latin and w['latin'] not in seen_in_pool:
                        review_pool.append(w)
                        seen_in_pool.add(w['latin'])

    # --- ШАГ 3: ВЫБИРАЕМ 3 СЛОВА ДЛЯ ПОВТОРА ---
    current_review = []
    if len(review_pool) >= 3:
        current_review = random.sample(review_pool, 3)
    else:
        current_review = review_pool # Если слов мало, берем сколько есть

    # --- ШАГ 4: ВЫБИРАЕМ 3 НОВЫХ СЛОВА ---
    # Собираем вообще все слова, которые когда-либо были в истории
    all_time_latin = set()
    for entry in history:
        if 'words' in entry:
            for w in entry['words']: all_time_latin.add(w['latin'])

    available_new = [w for w in data['words'] if w['latin'] not in all_time_latin]
    if len(available_new) < 3: available_new = data['words']
    
    new_words = random.sample(available_new, k=3)

    # --- ШАГ 5: ФОРМИРУЕМ СООБЩЕНИЕ ---
    full_message = ""
    if current_review:
        full_message += "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n"
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
    
    # Глубокая история для исключения повторов
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-500:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
