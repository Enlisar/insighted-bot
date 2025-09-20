import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --------------------------
# CONFIGURATION
# --------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN or OPENROUTER_API_KEY not set in environment variables")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --------------------------
# CHAT HISTORY STORAGE
# --------------------------
user_histories = {}

# --------------------------
# GPT FUNCTION USING OPENROUTER
# --------------------------
async def generate_reply(user_id, user_message: str) -> str:
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content":
             "You are InsightED, a kind and motivational mentor helping students stay in school. "
             "Be supportive, uplifting, and engaging. Encourage long conversations."}
        ]

    # Add user message
    user_histories[user_id].append({"role": "user", "content": user_message})

    # Call OpenRouter API
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openchat/openchat-7b:free",  # free model
            "messages": user_histories[user_id],
            "max_tokens": 400,
            "temperature": 0.9
        }
    )

    if response.status_code != 200:
        logger.error(f"OpenRouter Error: {response.text}")
        return "⚠️ Sorry, AI is currently unavailable. Try again later."

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    # Add bot reply to history
    user_histories[user_id].append({"role": "assistant", "content": reply})

    return reply

# --------------------------
# BOT COMMANDS
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        "👋 Hello, I am *InsightED Bot* 🌸 — your friendly study companion!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        "🌟 I am *InsightED Bot*, your supportive guide!\n\n👉 Use /start to begin chatting."
    )

# --------------------------
# CHAT HANDLER
# --------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text

    logger.info(f"Message from {user_id}: {user_message}")

    try:
        bot_reply = await generate_reply(user_id, user_message)
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")

# --------------------------
# MAIN FUNCTION
# --------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 InsightED Bot is running with OpenRouter...")
    app.run_polling()

if __name__ == "__main__":
    main()
