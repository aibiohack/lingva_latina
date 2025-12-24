import os, json, random, requests, sys
from datetime import datetime, timedelta

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def main():
    # Загружаем данные
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Загружаем историю (или создаем пустую)
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    today = datetime.now().strftime("%Y-%m-%d")
    mode = sys.argv[1] if len(sys.argv) > 1 else "words"
    message = ""

    # 1. ПРОВЕРКА ОБРАТНОГО ПОВТОРА (3 дня назад)
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    for entry in history:
        if entry['date'] == three_days_ago and entry['type'] == 'words':
            rev_words = entry['items']
            message += "🔄 <b>Обратный повтор (3 дня спустя):</b>\n"
            message += "Как это будет на латыни?\n"
            for w in rev_words:
                message += f"— {w['ru']} (?)\n"
            message += f"\n<tg-spoiler>Ответ: {', '.join([x['latin'] for x in rev_words])}</tg-spoiler>\n\n"

    # 2. ОТПРАВКА НОВОГО МАТЕРИАЛА
    if mode == "quote":
        q = random.choice(data['quotes'])
        message += f"📜 <b>Мудрость дня:</b>\n\n<i>{q['latin']}</i>\n— {q['ru']}"
        history.append({"date": today, "type": "quote", "items": [q]})
    else:
        new_words = random.sample(data['words'], k=3)
        message += "💡 <b>Новые слова:</b>\n\n" + "\n".join([f"• {w['latin']} — {w['ru']}" for w in new_words])
        history.append({"date": today, "type": "words", "items": new_words})

    # Сохраняем историю (только последние 30 дней, чтобы файл не раздувался)
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history[-50:], f, ensure_ascii=False, indent=2)

    send_message(message)

if __name__ == "__main__":
    main()
