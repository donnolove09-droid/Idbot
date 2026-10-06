# -*- coding: utf-8 -*-
"""bot.py — Bot trả mã code để user nhập vào web."""

import os
import random
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_URL = os.getenv("WEB_URL", "http://localhost:8080")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "changeme")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)


def gen_code() -> str:
    """Sinh mã 6 số ngẫu nhiên."""
    return f"{random.randint(100000, 999999)}"


def push_id_to_web(code: str, telegram_id: int) -> bool:
    """Gửi ID lên Flask qua API."""
    try:
        r = requests.post(
            f"{WEB_URL}/api/store",
            json={"code": code, "telegram_id": telegram_id},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=5
        )
        return r.json().get("ok", False)
    except Exception as e:
        log.error(f"push_id_to_web lỗi: {e}")
        return False


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    code = gen_code()

    ok = push_id_to_web(code, uid)

    if not ok:
        await update.message.reply_text(
            "❌ Không kết nối được web. Thử lại sau."
        )
        return

    text = (
        f"👋 Xin chào *{user.first_name}*!\n\n"
        f"🆔 ID Telegram của bạn:\n"
        f"`{uid}`\n\n"
        f"📋 *Mã tra cứu*: `{code}`\n\n"
        f"👉 Vào web để xác nhận:\n"
        f"{WEB_URL}\n\n"
        f"Nhập mã `{code}` vào web để hiện ID đầy đủ."
    )

    kb = [[InlineKeyboardButton("🌐 Mở web", url=WEB_URL)]]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"🆔 ID của bạn: `{uid}`",
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Hướng dẫn*\n\n"
        "• /start — Nhận mã để tra cứu ID trên web\n"
        "• /id — Xem ID trực tiếp\n"
        "• /help — Trợ giúp",
        parse_mode="Markdown"
    )


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ Thiếu BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    log.info("🤖 Bot chạy...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
