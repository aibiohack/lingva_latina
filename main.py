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
    
    # --- ШАГ 1: СОБИРАЕМ ВСЕ СЛОВА ДЛЯ ПОВТОРА (Вчера + 3 дня назад) ---
    review_pool = []
    target_dates = [
        (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    ]
    
    for entry in history:
        if entry['date'] in target_dates and 'words' in entry:
            review_pool.extend(entry['words'])

    # --- ШАГ 2: УДАЛЯЕМ ТЕ, ЧТО УЖЕ ПОВТОРЯЛИ СЕГОДНЯ ---
    already_reviewed_today = set()
    for entry in history:
        if entry['date'] == today_str:
            # Исключаем слова, которые были новыми сегодня
            if 'words' in entry:
                for w in entry['words']:
                    already_reviewed_today.add(w['latin'])
            # Исключаем слова, которые уже попадали в блок "Вспомнить" сегодня
            if 'reviewed_today' in entry:
                for w_latin in entry['reviewed_today']:
                    already_reviewed_today.add(w_latin)

    # Фильтруем пул: оставляем только те, что еще не мелькали сегодня
    filtered_review_pool = [w for w in review_pool if w['latin'] not in already_reviewed_today]

    # --- ШАГ 3: ВЫБИРАЕМ 3 СЛОВА ДЛЯ ПОВТОРА ---
    current_review_selection = []
    if filtered_review_pool:
        current_review_selection = random.sample(filtered_review_pool, min(3, len(filtered_review_pool)))
    elif review_pool:
        # Если все слова за вчера уже показаны, берем случайные из общего пула вчера
        current_review_selection = random.sample(review_pool, min(3, len(review_pool)))

    # --- ШАГ 4: ВЫБИРАЕМ 3 НОВЫХ СЛОВА (которых не было в истории вообще) ---
    all_time_seen = set()
    for entry in history:
        if 'words' in entry:
            for w in entry['words']:
                all_time_seen.add(w['latin'])

    available_new = [w for w in data['words'] if w['latin'] not in all_time_seen]
    if len(available_new) < 3: available_new = data['words']
    
    new_words = random.sample(available_new, k=3)

    # --- ШАГ 5: ФОРМИРУЕМ СООБЩЕНИЕ ---
    full_message = ""
    if current_review_selection:
        full_message += "🧠 <b>ВРЕМЯ ВСПОМНИТЬ:</b>\n\n"
        for w in current_review_selection:
            full_message += f"• {w['ru']} — <tg-spoiler>{w['latin']}</tg-spoiler>\n"
        full_message += "\n— — — — — — — —\n\n"

    if mode == "morning":
        q = random.choice(data['quotes'])
        full_message += f"📜 <b>МУДРОСТЬ ДНЯ:</b>\n<i>{q['latin']}</i>\n— {q['ru']}\n\n— — — — — — — —\n\n"

    full_message += "💡 <b>НОВЫЕ СЛОВА:</b>\n"
    full_message += "\n".join([f"• <b>{w['latin']}</b> — {w['ru']}" for w in new_words])

    # --- ШАГ 6: СОХРАНЯЕМ В ИСТОРИЮ (включая то, что повторили) ---
    history.append({
        "date": today_str,
        "words": new_words,
        "reviewed_today": [w['latin'] for w in current_review_selection] # ЗАПОМИНАЕМ ПОВТОР
    })
    
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-300:], f, ensure_ascii=False, indent=2)

    send_message(full_message)

if __name__ == "__main__":
    main()
