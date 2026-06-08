import logging
import os
from groq import Groq
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Tokenlar Render Environment Variables orqali olinadi
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Sen O'zbek tilida javob beradigan aqlli AI yordamchisan.
Barcha javoblarni O'zbek tilida ber.
"""

user_conversations = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []

    await update.message.reply_text(
        "Salom!\n\n"
        "Men AI yordamchi botman.\n"
        "Savolingizni yuboring.\n\n"
        "/clear - tarixni tozalash"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("Suhbat tarixi tozalandi.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append(
        {"role": "user", "content": text}
    )

    # Oxirgi 20 ta xabarni saqlash
    user_conversations[user_id] = user_conversations[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + user_conversations[user_id],
            temperature=0.7,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content

        user_conversations[user_id].append(
            {"role": "assistant", "content": answer}
        )

        await update.message.reply_text(answer)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text(
            "Xatolik yuz berdi. Keyinroq urinib ko'ring."
        )


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN topilmadi")

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY topilmadi")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
