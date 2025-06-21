import os
import logging
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
API_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [Your existing message handling logic]
    pass

async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [Your existing greeting logic]
    pass

async def main():
    application = Application.builder().token(API_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
    
    logger.info("🚀 Bot started!")
    await application.run_polling()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logger.error(f"⚠️ Restarting in 10 sec... Error: {e}")
            time.sleep(10)
            
