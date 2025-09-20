import logging
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --------------------------
# CONFIGURATION
# --------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN or OPENAI_API_KEY not set in environment variables")

# Groq client
client = OpenAI(api_key=OPENAI_API_KEY)

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
# GPT FUNCTION USING GROQ
# --------------------------
async def generate_reply(user_id, user_message: str) -> str:
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content":
             "You are InsightED, a kind and motivational mentor helping students stay in school. "
             "Be supportive, uplifting, and engaging. Encourage long conversations."}
        ]

    # add user message
    user_histories[user_id].append({"role": "user", "content": user_message})

    # get Groq chat reply
    response = client.chat.completions.create(
        model="groq-3.5-mini",
        messages=user_histories[user_id],
        max_tokens=400,
        temperature=0.9
    )

    reply = response.choices[0].message.content

    # add bot reply to history
    user_histories[user_id].append({"role": "assistant", "content": reply})

    return reply

# --------------------------
# BOT COMMANDS
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Hello, I am *InsightED Bot* 🌸 — your friendly study companion!\n\n"
        "I’ll help you stay strong even if you feel low about marks, attendance, or finances. 💡\n\n"
        "👉 Use /scholarships to explore financial aid options."
    )
    await update.message.reply_markdown(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 I am *InsightED Bot*, your supportive guide!\n\n"
        "💬 You can share your worries with me, like:\n"
        "- 'I am scared of failing in exams'\n"
        "- 'I have low attendance'\n"
        "- 'I may not afford fees'\n\n"
        "Commands:\n"
        "👉 /start - Introduction\n"
        "👉 /help - Guidance\n"
        "👉 /scholarships - Scholarship list 🎓"
    )
    await update.message.reply_markdown(help_text)

async def scholarships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scholarships_text = (
        "🎓 *Scholarship Opportunities for Students* \n\n"
        "🌍 *Global Scholarships:*\n"
        "1. [UNESCO Fellowships](https://www.unesco.org/fellowships)\n"
        "2. [Chevening Scholarships](https://www.chevening.org/)\n"
        "3. [Erasmus+](https://erasmus-plus.ec.europa.eu/)\n\n"
        "🇮🇳 *Indian Scholarships:*\n"
        "1. [National Scholarship Portal](https://scholarships.gov.in/)\n"
        "2. [INSPIRE Scholarship](https://online-inspire.gov.in/)\n"
        "3. [AICTE Pragati & Saksham](https://www.aicte-india.org/schemes/students-development-schemes)\n\n"
        "🇺🇸 *US Scholarships:*\n"
        "1. [Fulbright Program](https://foreign.fulbrightonline.org/)\n"
        "2. [Gates Millennium Scholars](https://gmsp.org/)\n"
        "3. [FAFSA Grants](https://studentaid.gov/)\n\n"
        "💡 Apply early & keep documents ready!"
    )
    await update.message.reply_markdown(scholarships_text)

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
        await update.message.reply_text("⚠️ Sorry, something went wrong. Please try again.")

# --------------------------
# MAIN FUNCTION
# --------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("scholarships", scholarships))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 InsightED Bot is running with Groq...")
    app.run_polling()

if __name__ == "__main__":
    main()
