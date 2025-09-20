import logging
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --------------------------
# CONFIGURATION
# --------------------------
# TELEGRAM_TOKEN = "7593620257:AAEORZ3ElqqSWnagMZqnF742ZHT5rg5pxHU"
# openai.api_key = "sk-...yPQA"

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --------------------------
# GPT FUNCTION
# --------------------------
async def generate_reply(user_message: str) -> str:
    prompt = f"""
    You are 'codered', a kind, polite, and motivational chatbot helping students 
    overcome fear of low marks, low attendance, or socio-economic issues 
    that might lead to dropping out. Your tone is warm, friendly, and uplifting.  

    Goals:
    - Encourage students with motivational quotes about never giving up.
    - Suggest ways to improve academics & attendance.
    - If relevant, mention scholarships (but remind them they can use /scholarships command for details).
    - Help them realise and correct their mistakes without guilt-tripping.  
    - Leave them feeling hopeful and motivated.  

    Student said: "{user_message}"
    InsightED reply:
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.8
    )
    return response.choices[0].message["content"]

# --------------------------
# BOT COMMANDS
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Hello, I am *codered* 🌸 — your friendly study companion! \n\n"
        "My purpose is to help you stay strong in your journey, even if you feel low about marks, "
        "attendance, or finances. 💡\n\n"
        "I’ll share motivational quotes, guidance, and information about scholarships that might help. "
        "Just tell me what’s on your mind, and we’ll work it out together 🤝.\n\n"
        "👉 Use /scholarships to explore financial aid options."
    )
    await update.message.reply_markdown(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 I am *codered2312*, your supportive guide!\n\n"
        "💬 You can share your worries with me, like:\n"
        "- 'I am scared of failing in exams'\n"
        "- 'I have low attendance'\n"
        "- 'I may not afford fees'\n\n"
        "Commands you can try:\n"
        "👉 /start - Introduction\n"
        "👉 /help - Guidance on how to talk to me\n"
        "👉 /scholarships - Get a list of scholarship schemes 🎓"
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
        "💡 *Pro Tip:* Apply early and keep documents (marksheets, ID, income certificate) ready."
    )
    await update.message.reply_markdown(scholarships_text)

# --------------------------
# CHAT HANDLER
# --------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    bot_reply = await generate_reply(user_message)
    await update.message.reply_text(bot_reply)



# # store per-user history
# user_histories = {}

# async def generate_reply(user_id, user_message: str) -> str:
#     if user_id not in user_histories:
#         user_histories[user_id] = [
#             {"role": "system", "content": 
#              "You are InsightED, a kind and motivational mentor helping students stay in school. "
#              "Be supportive, uplifting, and engaging. Encourage long conversations."}
#         ]

#     # add user message
#     user_histories[user_id].append({"role": "user", "content": user_message})

#     # get GPT reply
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=user_histories[user_id],
#         max_tokens=400,
#         temperature=0.9
#     )

#     reply = response.choices[0].message["content"]

#     # add bot reply to history
#     user_histories[user_id].append({"role": "assistant", "content": reply})

#     return reply    

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

    print("🤖 codered is running...")
    app.run_polling()

if __name__ == "__main__":
    main()