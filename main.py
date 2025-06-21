import os
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import httpx
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(simple_responses[key])
        return

    if "я думаю інакше" in key:
        await update.message.reply_text("Цікава думка! Можеш розповісти більше про Clash of Clans?")
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
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        ai_reply = "Вибач, сталася помилка при спробі відповісти."

    await update.message.reply_text(ai_reply)

async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        name = member.first_name or "новачок"
        await update.message.reply_text(
            f"Ласкаво просимо в групу, {name}! 🎉 "
            "Якщо маєш питання по Clash of Clans — пиши мені!"
        )

async def main():
    """Run the bot."""
    application = Application.builder().token(API_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
    
    logging.info("🚀 Бот запущено! / Bot started!")
    await application.run_polling()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logging.error(f"⚠️ Збій! Перезапуск через 10 сек... / Crash! Restarting in 10 sec... Error: {e}")
            time.sleep(10)
