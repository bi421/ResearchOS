# scripts/bot_server.py
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

# .env-ээс токен унших
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

# Root хавтас руу зам нэмэх (researchos импортлох)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from researchos.result_cache import load_cache, save_cache, update_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# КОМАНДУУД
# ============================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 *ResearchOS Bot* ажиллаж байна.\n\n/status – сүүлийн үр дүн (хурдан)\n/update – шинжилгээг шинэчлэх (дэвсгэрт)\n/run – шинжилгээг шууд ажиллуулж, үр дүнг харуулах (удаан)", parse_mode="Markdown")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cache = load_cache()
    if not cache:
        await update.message.reply_text("⚠️ Кэш хоосон. /update командыг ашиглана уу.")
        return
    text = f"📊 *Сүүлийн шинжилгээ* ({cache.get('timestamp', '')})\nBacktest өгөөж: {cache.get('backtest_return', 'N/A')}%\nML дохио: {cache.get('ml_signal', 'N/A')}\nШийдвэр: {cache.get('decision', 'N/A')}\nШалтгаан: {cache.get('reason', '')}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Шинжилгээг шинэчилж байна... (дэвсгэрт ажиллах болно)")
    asyncio.create_task(run_update_background(update))


async def run_update_background(update: Update):
    try:
        data = update_cache()  # main.py ажиллуулна
        save_cache(data)
        await update.message.reply_text("✅ Шинжилгээ амжилттай шинэчлэгдлээ. /status-ээр харна уу.")
    except Exception as e:
        logger.exception("Update failed")
        await update.message.reply_text(f"❌ Алдаа: {e}")


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Шинжилгээг шууд ажиллуулж байна... (хэдэн минут шаардагдана)")
    try:
        result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, cwd=ROOT)
        output = result.stdout + result.stderr
        if len(output) > 4000:
            for i in range(0, len(output), 4000):
                await update.message.reply_text(f"```\n{output[i : i + 4000]}\n```", parse_mode="MarkdownV2")
        else:
            await update.message.reply_text(f"✅ Дууссан.\n\n```\n{output}\n```", parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"❌ Алдаа: {e}")


# ============================================================
# БОТЫГ ЭХЛҮҮЛЭХ
# ============================================================


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("update", update_command))
    app.add_handler(CommandHandler("run", run_command))
    logger.info("🤖 Bot started (cache mode)")
    app.run_polling()


if __name__ == "__main__":
    main()
