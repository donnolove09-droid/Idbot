# -*- coding: utf-8 -*-
"""app.py — Web hiển thị ID Telegram."""

import os
import threading
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Lưu tạm ID trong RAM: {code: telegram_id}
# (Đơn giản, không dùng DB)
ID_STORE = {}
LOCK = threading.Lock()

# Thông tin bot
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot")
WEB_URL = os.getenv("WEB_URL", "http://localhost:8080")


@app.route("/")
def index():
    return render_template("index.html",
                           bot_username=BOT_USERNAME,
                           web_url=WEB_URL)


@app.route("/api/verify", methods=["POST"])
def verify():
    """
    User nhập mã code (VD: 123456) → web trả ID.
    """
    code = (request.json or {}).get("code", "").strip()
    if not code:
        return jsonify({"ok": False, "error": "Chưa nhập mã"})

    with LOCK:
        tg_id = ID_STORE.get(code)

    if not tg_id:
        return jsonify({"ok": False, "error": "Mã không tồn tại hoặc đã hết hạn"})

    # Xóa mã sau khi dùng (1 lần)
    with LOCK:
        ID_STORE.pop(code, None)

    return jsonify({"ok": True, "telegram_id": tg_id})


@app.route("/api/store", methods=["POST"])
def store():
    """
    Bot gọi API này để lưu ID với code.
    (Chỉ dùng nội bộ, nên có secret key)
    """
    secret = os.getenv("INTERNAL_SECRET", "changeme")
    if request.headers.get("X-Internal-Secret") != secret:
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    data = request.json or {}
    code = data.get("code", "").strip()
    tg_id = data.get("telegram_id")

    if not code or not tg_id:
        return jsonify({"ok": False, "error": "Thiếu dữ liệu"})

    with LOCK:
        ID_STORE[code] = int(tg_id)

    return jsonify({"ok": True})


@app.route("/health")
def health():
    return jsonify({"ok": True, "stored": len(ID_STORE)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
