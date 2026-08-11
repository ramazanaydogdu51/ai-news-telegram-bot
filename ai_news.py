import requests
import os
from datetime import datetime

NEWSAPI_KEY = os.environ["NEWSAPI_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def translate_to_turkish(text):
    if not text:
        return text
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|tr"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["responseData"]["translatedText"]
    except Exception:
        return text


def fetch_ai_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "artificial intelligence",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 6,
        "apiKey": NEWSAPI_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("articles", [])


def build_message(articles):
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"AI Haberleri - {today}", ""]
    for i, article in enumerate(articles, 1):
        title_tr = translate_to_turkish(article.get("title") or "")
        desc_tr = translate_to_turkish(article.get("description") or "")
        url = article.get("url", "")
        lines.append(f"{i}. {title_tr}")
        if desc_tr:
            lines.append(desc_tr)
        if url:
            lines.append(url)
        lines.append("")
    return "\n".join(lines)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()


def main():
    articles = fetch_ai_news()
    if not articles:
        send_telegram("Bugun icin AI haberi bulunamadi.")
        return
    send_telegram(build_message(articles))
    print("Mesaj gonderildi.")


if __name__ == "__main__":
    main()
