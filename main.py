import os
import json
import random
import requests
import sys

TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TG_CHAT_ID')

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    
    # Добавляем проверку отправки
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Сообщение успешно отправлено в Telegram!")
    else:
        print(f"❌ Ошибка отправки! Код: {response.status_code}")
        print(f"Ответ сервера: {response.text}")

def main():
    print("🚀 Запуск скрипта...")
    
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при чтении файла data.json: {e}")
        return

    mode = sys.argv[1] if len(sys.argv) > 1 else "words"
    print(f"📊 Режим работы: {mode}")

    if mode == "quote":
        q = random.choice(data['quotes'])
        message = f"📜 <b>Мудрость дня:</b>\n\n<i>{q['latin']}</i>\n— {q['ru']}"
    else:
        words = random.sample(data['words'], k=min(3, len(data['words'])))
        message = "💡 <b>Новые слова:</b>\n\n" + "\n".join([f"• {w['latin']} — {w['ru']}" for w in words])

    send_message(message)

if __name__ == "__main__":
    main()
