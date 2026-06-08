     import logging
import os
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================
# SOZLAMALAR
# =============================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")

# Groq mijozi
client = Groq(api_key=GROQ_API_KEY)

# Har bir foydalanuvchi uchun suhbat tarixi
user_conversations = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Sen O'zbek tilida javob beradigan aqlli yordamchi botsan.
Foydalanuvchilar bilan do'stona, qisqa va aniq muloqot qil.
Barcha javoblarni faqat O'zbek tilida ber.
Agar savol tushunarsiz bo'lsa, qayta so'ra."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text(
        "👋 Salom! Men AI yordamchi botman.\n\n"
        "Istalgan savolingizni yozing — javob beraman! 🤖\n\n"
        "📌 Buyruqlar:\n"
        "/start — Botni qayta boshlash\n"
        "/clear — Suhbat tarixini tozalash\n"
        "/help — Yordam"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✅ Suhbat tarixi tozalandi!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "Bu bot Groq AI yordamida ishlaydi.\n\n"
        "• Istalgan savol yozing\n"
        "• Bot O'zbek tilida javob beradi\n"
        "• /clear — Suhbatni tozalash\n\n"
        "Savolingizni yozing! 😊",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_conversations:
        user_conversations[user_id] = []

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    user_conversations[user_id].append({
        "role": "user",
        "content": user_text
    })

    if len(user_conversations[user_id]) > 20:
        user_conversations[user_id] = user_conversations[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *user_conversations[user_id]
            ],
            max_tokens=1024
        )

        bot_reply = response.choices[0].message.content

        user_conversations[user_id].append({
            "role": "assistant",
            "content": bot_reply
        })

        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(
            "⚠️ Kechirasiz, xato yuz berdi. Qaytadan urinib ko'ring."
        )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()   
