import logging
import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langdetect import detect

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
# HELPLINE INFO
# --------------------------
HELPLINES_EN = """
Here are some helpline numbers you might find helpful:

- Mental Health Support: 9152987821 (Vandrevala Foundation)
- Women's Helpline: 1091
- Child Helpline: 1098
- General Emergency: 112

Remember, seeking help is a sign of strength.
"""

HELPLINES_HI = """
यदि आपको मदद चाहिए, तो ये हेल्पलाइन नंबर उपयोगी हो सकते हैं:

- मानसिक स्वास्थ्य सहायता: 9152987821 (Vandrevala Foundation)
- महिला हेल्पलाइन: 1091
- बाल हेल्पलाइन: 1098
- आपातकालीन सेवा: 112

मदद मांगना साहस की निशानी है।
"""

# --------------------------
# USER HISTORY STORAGE
# --------------------------
user_histories = {}

# Keywords related to sensitive issues to detect
SENSITIVE_KEYWORDS = [
    "mental health", "family pressure", "social stigma",
    "डर", "परेशानी", "दबाव", "तनाव", "घर", "परिवार", "लड़की", "छात्रा", "छात्र",
    "drop out", "dropping out", "left school", "failed", "anxiety", "depression"
]

def contains_sensitive_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SENSITIVE_KEYWORDS)

def is_hindi(text: str) -> bool:
    try:
        return detect(text) == 'hi'
    except:
        return False

def build_system_prompt(user_message: str, use_hindi: bool) -> str:
    if contains_sensitive_keyword(user_message):
        # Sensitive message → motivational + helplines
        if use_hindi:
            return (
                "आप एक सहायक, दयालु, और प्रेरक मेंटर हैं जो छात्रों को पढ़ाई छोड़ने के कारणों से लड़ने में मदद करता है, "
                "खासतौर पर मानसिक स्वास्थ्य, परिवार का दबाव (खासकर लड़कियों के लिए), और सामाजिक कलंक। "
                "आपका स्वर स्नेहपूर्ण, सहानुभूतिपूर्ण, और उत्साहवर्धक है।\n"
                f"छात्र ने कहा: \"{user_message}\"\n"
                "कृपया उन्हें प्रोत्साहित करें और आवश्यक हेल्पलाइन नंबर दें।"
            )
        else:
            return (
                "You are a kind, gentle, and motivational mentor helping students overcome reasons that lead to dropping out, "
                "especially mental health, family pressure (especially for girls), and social stigma. "
                "Your tone is warm, empathetic, and encouraging.\n"
                f"Student said: \"{user_message}\"\n"
                "Please motivate them and provide relevant helpline numbers."
            )
    else:
        # Casual message → friendly chat only, no helplines
        if use_hindi:
            return (
                "आप एक दोस्ताना और सहायक चैटबोट हैं। "
                "छात्र के साथ हल्की, सकारात्मक और मित्रवत बातचीत करें।\n"
                f"छात्र ने कहा: \"{user_message}\""
            )
        else:
            return (
                "You are a friendly and supportive chatbot. "
                "Chat in a light, positive, and engaging manner.\n"
                f"Student said: \"{user_message}\""
            )


# --------------------------
# GPT CALL WITH HISTORY (OpenRouter)
# --------------------------
async def generate_reply(user_id: int, user_message: str) -> str:
    use_hindi = is_hindi(user_message)

    if user_id not in user_histories:
        system_content = (
            "You are InsightED, a kind and motivational mentor helping students stay in school. "
            "Be supportive, uplifting, and engaging. Encourage long conversations."
        )
        user_histories[user_id] = [{"role": "system", "content": system_content}]

    # Add user message
    prompt = build_system_prompt(user_message, use_hindi)
    user_histories[user_id].append({"role": "user", "content": prompt})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:3000",  # replace with your project URL if hosted
                "X-Title": "InsightED Bot",
            },
            json={
                "model": "openai/gpt-4o-mini",  # you can swap this model
                "messages": user_histories[user_id],
                "max_tokens": 400,
                "temperature": 0.8,
            },
            timeout=60.0
        )

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    # Save assistant reply
    user_histories[user_id].append({"role": "assistant", "content": reply})

    return reply

# --------------------------
# BOT COMMANDS
# --------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Hello, I am *InsightED* 🌸 — your friendly study companion!\n\n"
        "My purpose is to help you stay strong in your journey, even if you feel low about marks, "
        "attendance, or finances. 💡\n\n"
        "I’ll share motivational quotes, guidance, and information about scholarships that might help. "
        "Just tell me what’s on your mind, and we’ll work it out together 🤝.\n\n"
        "👉 Use /scholarships to explore financial aid options."
    )
    await update.message.reply_markdown(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 I am *InsightED*, your supportive guide!\n\n"
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
# MESSAGE HANDLER
# --------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id

    try:
        reply = await generate_reply(user_id, user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong.")

# --------------------------
# MAIN FUNCTION
# --------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("scholarships", scholarships))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 InsightED Bot is running with OpenRouter...")
    app.run_polling()

if __name__ == "__main__":
    main()
