import requests
import re
import csv
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = "8504331141:AAEJqw8XSi_LEzLI7vNfzfiuxp0WDgNGtu0"

# 🔍 IBAN zoeken
def extract_iban(text):
    clean_text = text.replace(" ", "")
    match = re.search(r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{10,30}\b', clean_text)
    return match.group(0) if match else None

# 💾 opslaan (alleen IBAN + bank → veiliger)
def save_to_file(iban, bank):
    with open("iban_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), iban, bank])

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stuur je tekst met IBAN, ik voeg de bank toe 💳")

# 🧠 verwerking
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    original_text = update.message.text

    iban = extract_iban(original_text)

    if not iban:
        await update.message.reply_text("❌ Geen IBAN gevonden")
        return

    url = f"https://openiban.com/validate/{iban}?getBIC=true&validateBankCode=true"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        if not data.get("valid"):
            await update.message.reply_text("❌ Ongeldige IBAN")
            return

        bank_name = data.get("bankData", {}).get("name", "Onbekend")

        # 💾 opslaan
        save_to_file(iban, bank_name)

        # 📤 originele tekst + bank
        response = f"""{original_text}

🏦 Bank: {bank_name}
"""

        await update.message.reply_text(response)

    except Exception:
        await update.message.reply_text("⚠️ API fout")

# 📤 export functie
async def export_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("iban_log.csv", "rb") as f:
            await update.message.reply_document(f, filename="iban_log.csv")
    except:
        await update.message.reply_text("Nog geen data opgeslagen.")

# ⚙️ setup
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("export", export_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot draait...")
app.run_polling()