import os
import logging
import asyncio
import threading
import sys
import random
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
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

# --- GREATNESS QUOTES (30 TOTAL) ---
MOTIVATION_QUOTES = [
    "Greatness is not a function of circumstance; greatness is a matter of conscious choice.",
    "The secret of your future is hidden in your daily routine.",
    "Don't be afraid to give up the good to go for the great.",
    "The only way to achieve greatness is to love what you do.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "Greatness is won, not given. It is the result of tireless effort.",
    "To be great, you must be willing to be misunderstood, criticized, and doubted.",
    "He who is not courageous enough to take risks will accomplish nothing in life.",
    "The distance between dreams and reality is called discipline.",
    "Stop chasing the money and start chasing the passion and the greatness.",
    "Greatness lives in the heart of the person who refuses to settle for average.",
    "You were born to be great, but you must choose to be great every single day.",
    "Success is walking from failure to failure with no loss of enthusiasm.",
    "Your greatness is revealed not by the lights that shine on you, but by the light that shines within you.",
    "Small deeds done are better than great deeds planned.",
    "The quality of a man's life is in direct proportion to his commitment to excellence.",
    "Don't wait for opportunity. Create it.",
    "Great minds discuss ideas; average minds discuss events; small minds discuss people.",
    "If you want to be great, you have to stop asking for permission.",
    "Greatness is found in the struggle, not the victory.",
    "Everything you've ever wanted is on the other side of fear.",
    "The only limit to our realization of tomorrow will be our doubts of today.",
    "Do not pray for an easy life, pray for the strength to endure a difficult one.",
    "Hard work beats talent when talent doesn't work hard.",
    "Greatness is the ability to maintain focus when everything around you is chaotic.",
    "Your life does not get better by chance, it gets better by change.",
    "Success isn't always about greatness. It's about consistency.",
    "Be so good they can't ignore you.",
    "A great person is one who makes everyone else feel great.",
    "The path to greatness is often a lonely one. Keep walking."
]

# --- BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the 2-hour motivation cycle."""
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name

    # Remove existing jobs to avoid multiple cycles
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Schedule the 2-hour recurring motivation
    context.job_queue.run_repeating(
        send_motivation, 
        interval=timedelta(hours=2), 
        first=0, # Send the first one immediately
        chat_id=chat_id, 
        name=str(chat_id)
    )

    logger.info(f"Motivation cycle started for {user_name} ({chat_id})")
    await update.message.reply_text(
        f"Hello {user_name}! 🌟\n\n"
        "Your journey to greatness begins now.\n"
        "I will send you powerful motivation every 2 hours to keep your fire burning.\n\n"
        "Stay focused. Stay great."
    )

async def send_motivation(context: ContextTypes.DEFAULT_TYPE):
    """Callback to send a random quote."""
    job = context.job()
    quote = random.choice(MOTIVATION_QUOTES)
    
    text = f"🚀 **TIME TO BE GREAT**\n\n\"{quote}\"\n\nKeep pushing forward!"
    
    await context.bot.send_message(
        chat_id=job.chat_id, 
        text=text,
        parse_mode='Markdown'
    )

# --- RENDER HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Greatness Bot is active")
    def log_message(self, format, *args): return

def run_health_check():
    httpd = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    httpd.serve_forever()

# --- MAIN ---
async def main():
    # Run health check server in background
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
