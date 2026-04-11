import os
import logging
import asyncio
import threading
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!")
    sys.exit(1)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- TRANSLATIONS ---
STRINGS = {
    'en': {
        'welcome': "Welcome! Please select your language:",
        'select_time': "Choose a reminder duration:",
        'min_10': "10 Minutes",
        'min_30': "30 Minutes",
        'hour_1': "1 Hour",
        'set': "✅ Reminder set for {}!",
        'alarm': "⏰ **TIME IS UP!** This is your {} reminder.",
        'back': "Back to Language Selection"
    },
    'ko': {
        'welcome': "환영합니다! 언어를 선택해주세요:",
        'select_time': "알림 시간을 선택하세요:",
        'min_10': "10분",
        'min_30': "30분",
        'hour_1': "1시간",
        'set': "✅ {} 후에 알림이 울립니다!",
        'alarm': "⏰ **시간이 다 되었습니다!** {} 알림입니다.",
        'back': "언어 선택으로 돌아가기"
    },
    'tr': {
        'welcome': "Hoş geldiniz! Lütfen dilinizi seçin:",
        'select_time': "Hatırlatıcı süresini seçin:",
        'min_10': "10 Dakika",
        'min_30': "30 Dakika",
        'hour_1': "1 Saat",
        'set': "✅ {} için hatırlatıcı kuruldu!",
        'alarm': "⏰ **SÜRE DOLDU!** Bu sizin {} hatırlatıcınız.",
        'back': "Dil Seçimine Dön"
    }
}

# --- BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Language Selection"""
    keyboard = [
        [
            InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
            InlineKeyboardButton("한국어 🇰🇷", callback_data="lang_ko"),
            InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(STRINGS['en']['welcome'], reply_markup=reply_markup)
    else:
        # If called from a callback query (back button)
        await update.callback_query.edit_message_text(STRINGS['en']['welcome'], reply_markup=reply_markup)

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows reminder options after language is chosen"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang # Save preference
    
    s = STRINGS[lang]
    keyboard = [
        [InlineKeyboardButton(s['min_10'], callback_data="time_600_10m")],
        [InlineKeyboardButton(s['min_30'], callback_data="time_1800_30m")],
        [InlineKeyboardButton(s['hour_1'], callback_data="time_3600_1h")],
        [InlineKeyboardButton(f"⬅️ {s['back']}", callback_data="start_over")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=s['select_time'], reply_markup=reply_markup)

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedules the reminder using JobQueue"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    seconds = int(parts[1])
    label_key = parts[2] # 10m, 30m, 1h
    
    lang = context.user_data.get('lang', 'en')
    s = STRINGS[lang]
    
    # Determine the display label for the confirmation message
    if label_key == "10m": label = s['min_10']
    elif label_key == "30m": label = s['min_30']
    else: label = s['hour_1']

    chat_id = update.effective_chat.id
    
    # Schedule the job
    context.job_queue.run_once(
        send_alarm, 
        seconds, 
        chat_id=chat_id, 
        name=str(chat_id), 
        data={'lang': lang, 'label': label}
    )
    
    await query.edit_message_text(text=s['set'].format(label))

async def send_alarm(context: ContextTypes.DEFAULT_TYPE):
    """Callback function for the JobQueue when time is up"""
    job = context.job
    lang = job.data['lang']
    label = job.data['label']
    
    message = STRINGS[lang]['alarm'].format(label)
    await context.bot.send_message(job.chat_id, text=message, parse_mode='Markdown')

# --- RENDER HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Reminder Bot is active")
    def log_message(self, format, *args): return

def run_health_check():
    httpd = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    httpd.serve_forever()

# --- MAIN ---
def main():
    # Run health check server in background
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Initialize application with JobQueue enabled
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(start, pattern="^start_over$"))
    application.add_handler(CallbackQueryHandler(language_choice, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(set_reminder, pattern="^time_"))

    logger.info(f"Bot started on port {PORT}")
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
