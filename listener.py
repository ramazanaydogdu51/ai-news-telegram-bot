import json
import os
import requests

from news_lib import (
    TELEGRAM_TOKEN,
    build_ai_digest,
    build_tr_digest,
    build_world_digest,
    send_menu,
    send_telegram,
)

OFFSET_FILE = "offset.json"

DIGEST_BUILDERS = {
    "tr": build_tr_digest,
    "world": build_world_digest,
    "ai": build_ai_digest,
}


def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)


def answer_callback_query(callback_query_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_query_id}, timeout=15)


def get_updates(offset):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=20)
    resp.raise_for_status()
    return resp.json().get("result", [])


def main():
    offset = load_offset()
    updates = get_updates(offset)

    for update in updates:
        offset = max(offset, update["update_id"] + 1)

        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            send_menu(chat_id)

        elif "callback_query" in update:
            cq = update["callback_query"]
            answer_callback_query(cq["id"])
            data = cq.get("data")
            chat_id = cq["message"]["chat"]["id"]
            builder = DIGEST_BUILDERS.get(data)
            if builder:
                send_telegram(builder(), chat_id)

    save_offset(offset)


if __name__ == "__main__":
    main()
