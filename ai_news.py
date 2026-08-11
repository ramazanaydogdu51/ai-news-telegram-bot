import os
from news_lib import build_ai_digest, send_telegram

CHAT_ID = os.environ["CHAT_ID"]


def main():
    send_telegram(build_ai_digest(), CHAT_ID)
    print("Mesaj gonderildi.")


if __name__ == "__main__":
    main()
