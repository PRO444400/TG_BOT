import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import httpx
from dotenv import load_dotenv

load_dotenv()

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

    # Перевірка на слово "бот" або "bot" на початку чи в кінці
    if words[0] in ["бот", "bot"] or words[-1] in ["бот", "bot"]:
        return True

    # Перевірка на привітання + "бот" в тексті (наприклад, "привіт бот")
    greetings = ["привіт", "здрастуйте", "доброго дня", "добрий день", "доброго вечора"]
    if any(greet in words for greet in greetings) and ("бот" in words or "bot" in words):
        return True

    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if not should_respond(user_message):
        return  # Мовчимо, якщо не потрібно відповідати

    # Простих привітань без "бот" ігноруємо (тут лише обробка з "бот")
    # Якщо повідомлення містить прості фрази, але з "бот" — можемо відповісти статично
    simple_responses = {
        "привіт бот": "Привіт! Чим можу допомогти з Clash of Clans?",
        "здрастуйте бот": "Вітаю! Запитуйте про Clash of Clans.",
        "доброго дня бот": "Доброго дня! Чим допомогти у Clash of Clans?",
        "доброго вечора бот": "Доброго вечора! Питайте, якщо потрібна допомога з Clash of Clans.",
        "дякую бот": "Радий допомогти!",
        "спасибі бот": "Будь ласка!"
    }

    # Виводимо ключ без зайвих пробілів для порівняння
    key = user_message.lower().strip()

    if key in simple_responses:
        await update.message.reply_text(simple_responses[key])
        return

    # Якщо фраза "я думаю інакше" — відповідаємо шаблоном
    if "я думаю інакше" in key:
        await update.message.reply_text("Цікава думка! Можеш розповісти більше про Clash of Clans?")
        return

    # Запит до OpenRouter (GPT) тільки для складних повідомлень
    prompt = [
        {"role": "system", "content": "Ти експерт з гри Clash of Clans. Відповідай лише на запитання або теми, пов'язані з Clash of Clans. Якщо питання не про цю гру, ввічливо скажи, що можеш допомогти тільки з Clash of Clans, Але якщо привітання або прості слова не запитання на інші теми то можеш відповісти."},
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
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        ai_reply = "Вибач, сталася помилка при спробі відповісти."

    await update.message.reply_text(ai_reply)


# Вітання нових учасників у групі
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        name = member.first_name or "новачок"
        await update.message.reply_text(f"Ласкаво просимо в групу, {name}! 🎉 Якщо маєш питання по Clash of Clans — пиши мені!")


if __name__ == "__main__":
    app = ApplicationBuilder().token(API_TOKEN).build()

    # Обробка текстових повідомлень
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обробка нових учасників групи
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))

    print("Бот запущено...")
    app.run_polling()
