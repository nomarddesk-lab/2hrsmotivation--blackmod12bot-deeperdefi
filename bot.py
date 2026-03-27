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
)

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", 8080))
CHANNEL_LINK = "https://t.me/brosmasters" 
CHANNEL_NAME = "포커브로스 판다 클럽"

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!")
    sys.exit(1)

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcomes the user in Korean and provides the channel link for bonuses."""
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name

    # Create the redirection button
    keyboard = [
        [InlineKeyboardButton("📢 채널 가입하고 무료 선물 받기", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(f"User {user_name} ({chat_id}) started the bot.")
    
    # Promotional message in Korean
    welcome_message = (
        f"안녕하세요, {user_name}님! 🌟\n\n"
        f"**{CHANNEL_NAME}**에 오신 것을 환영합니다!\n\n"
        "🎁 **독점 혜택 안내:**\n"
        "• 지금 채널 가입 시 무료 보너스 증정\n"
        "• 100% 무료 회원가입 가능\n"
        "• 가입 즉시 특별 무료 선물 잠금 해제\n\n"
        "아래 버튼을 클릭하여 지금 바로 혜택을 확인하세요!"
    )

    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# --- RENDER HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Channel Redirection Bot is active")
    def log_message(self, format, *args): return

def run_health_check():
    httpd = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    httpd.serve_forever()

# --- MAIN ---
async def main():
    # Run health check server in background (useful for keeping the bot alive on services like Render)
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Initialize application
    application = ApplicationBuilder().token(TOKEN).build()

    # Simple command handler
    application.add_handler(CommandHandler('start', start))

    async with application:
        await application.initialize()
        await application.start()
        logger.info(f"Bot started on port {PORT}")
        await application.updater.start_polling()
        # Keep running
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
