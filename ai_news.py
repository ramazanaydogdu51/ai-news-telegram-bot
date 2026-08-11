import os
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FEEDS = [
    ("AI Weekly", "https://aiweekly.co/issues.rss", 2),
    ("Times of AI", "https://www.timesofai.com/feed/", 3),
    ("ScienceDaily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", 2),
]


def strip_html(text):
    return re.sub("<[^<]+?>", "", text or "").strip()


def translate_to_turkish(text):
    if not text:
        return text
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:490], "langpair": "en|tr"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["responseData"]["translatedText"]
    except Exception:
        return text


def fetch_feed(url, limit):
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        desc = strip_html(item.findtext("description") or "")
        link = (item.findtext("link") or "").strip()
        items.append({"title": title, "desc": desc, "link": link})
    return items


def build_message():
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"AI Haberleri - {today}", ""]
    for source_name, url, limit in FEEDS:
        try:
            items = fetch_feed(url, limit)
        except Exception:
            continue
        if not items:
            continue
        lines.append(f"--- {source_name} ---")
        for item in items:
            title_tr = translate_to_turkish(item["title"])
            desc_tr = translate_to_turkish(item["desc"][:400])
            lines.append(title_tr)
            if desc_tr:
                lines.append(desc_tr)
            if item["link"]:
                lines.append(item["link"])
            lines.append("")
    return "\n".join(lines)


def send_telegram(message):
    if len(message) > 4000:
        message = message[:3990] + "\n..."
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
    message = build_message()
    if not message.strip():
        send_telegram("Bugun icin AI haberi bulunamadi.")
        return
    send_telegram(message)
    print("Mesaj gonderildi.")


if __name__ == "__main__":
    main()
