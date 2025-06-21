import os
import logging
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import httpx
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Load environment variables
load_dotenv()

# ===== Flask Keep-Alive Server =====
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Бот працює! / Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Start Flask in a separate thread
Thread(target=run_flask, daemon=True).start()

# ===== Bot Configuration =====
API_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def should_respond(text: str) -> bool:
    text_lower = text.lower().strip()
    words = text_lower.split()

    if not words:
        return False

    if words[0] in ["бот", "bot"] or words[-1] in ["бот", "bot"]:
        return True

    greetings = ["привіт", "здрастуйте", "доброго дня", "добрий день", "доброго вечора"]
    if any(greet in words for greet in greetings) and ("бот" in words or "bot" in words):
        return True

    return False

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text

    if not should_respond(user_message):
        return

    simple_responses = {
        "привіт бот": "Привіт! Чим можу допомогти з Clash of Clans?",
        "здрастуйте бот": "Вітаю! Запитуйте про Clash of Clans.",
        "доброго дня бот": "Доброго дня! Чим допомогти у Clash of Clans?",
        "доброго вечора бот": "Доброго вечора! Питайте, якщо потрібна допомога з Clash of Clans.",
        "дякую бот": "Радий допомогти!",
        "спасибі бот": "Будь ласка!"
    }

    key = user_message.lower().strip()

    if key in simple_responses:
        update.message.reply_text(simple_responses[key])
        return

    if "я думаю інакше" in key:
        update.message.reply_text("Цікава думка! Можеш розповісти більше про Clash of Clans?")
        return

    prompt = [
        {
            "role": "system",
            "content": "Ти експерт з гри Clash of Clans. Відповідай лише на запитання або теми, пов'язані з Clash of Clans."
        },
        {"role": "user", "content": user_message}
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    json_data = {
        "model": "gpt-4o-mini",
        "messages": prompt,
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 1
    }

    try:
        with httpx.Client() as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        ai_reply = "Вибач, сталася помилка при спробі відповісти."

    update.message.reply_text(ai_reply)

def greet_new_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        name = member.first_name or "новачок"
        update.message.reply_text(
            f"Ласкаво просимо в групу, {name}! 🎉 "
            "Якщо маєш питання по Clash of Clans — пиши мені!"
        )

def main():
    while True:
        try:
            updater = Updater(API_TOKEN, use_context=True)
            dp = updater.dispatcher
            
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
            dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, greet_new_member))
            
            logging.info("🚀 Бот запущено! / Bot started!")
            updater.start_polling()
            updater.idle()
            
        except Exception as e:
            logging.error(f"⚠️ Збій! Перезапуск через 10 сек... / Crash! Restarting in 10 sec... Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
    
