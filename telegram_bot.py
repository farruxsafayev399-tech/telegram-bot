import logging
import os
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================
# SOZLAMALAR — shu yerga o'z tokenlaringizni kiriting
# =============================================
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"   # @BotFather dan olingan token
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY" # console.anthropic.com dan olingan kalit

# =============================================
# Claude mijozi
# =============================================
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Har bir foydalanuvchi uchun suhbat tarixi
user_conversations = {}

# Logging
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
    """Bot ishga tushganda birinchi xabar"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []  # Suhbat tarixini tozalash

    await update.message.reply_text(
        "👋 Salom! Men AI yordamchi botman.\n\n"
        "Istalgan savolingizni yozing — javob beraman! 🤖\n\n"
        "📌 Buyruqlar:\n"
        "/start — Botni qayta boshlash\n"
        "/clear — Suhbat tarixini tozalash\n"
        "/help — Yordam"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Suhbat tarixini tozalash"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✅ Suhbat tarixi tozalandi. Yangi suhbat boshlashingiz mumkin!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam xabari"""
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "Bu bot Claude AI yordamida ishlaydi.\n\n"
        "• Istalgan savol yozing\n"
        "• Bot O'zbek tilida javob beradi\n"
        "• /clear — Suhbatni tozalash\n\n"
        "Savolingizni yozing! 😊",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi xabarini Claude API orqali javoblash"""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Suhbat tarixini boshlash
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    # Yozmoqda... ko'rsatish
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Foydalanuvchi xabarini tarixga qo'shish
    user_conversations[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Tarixni 20 ta xabarga cheklash (xotira tejash)
    if len(user_conversations[user_id]) > 20:
        user_conversations[user_id] = user_conversations[user_id][-20:]

    try:
        # Claude API ga so'rov yuborish
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=user_conversations[user_id]
        )

        bot_reply = response.content[0].text

        # Bot javobini tarixga qo'shish
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
    """Botni ishga tushirish"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_command))

    # Oddiy xabarlar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
