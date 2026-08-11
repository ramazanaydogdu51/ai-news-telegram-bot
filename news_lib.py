import os
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")

AI_FEEDS = [
    ("AI Weekly", "https://aiweekly.co/issues.rss", 2),
    ("Times of AI", "https://www.timesofai.com/feed/", 3),
    ("ScienceDaily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", 2),
]

WORLD_DOMAINS = "bbc.co.uk,reuters.com,apnews.com,aljazeera.com,theguardian.com"


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


def fetch_rss(url, limit):
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


def build_ai_digest():
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"AI Haberleri - {today}", ""]
    found_any = False
    for source_name, url, limit in AI_FEEDS:
        try:
            items = fetch_rss(url, limit)
        except Exception:
            continue
        if not items:
            continue
        found_any = True
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
    if not found_any:
        return "Bugun icin AI haberi bulunamadi."
    return "\n".join(lines)


def build_tr_digest():
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"Turkiye Gundemi - {today}", ""]
    resp = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={"country": "tr", "pageSize": 6, "apiKey": NEWSAPI_KEY},
        timeout=15,
    )
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    if not articles:
        return "Bugun icin Turkiye gundemi haberi bulunamadi."
    for a in articles:
        title = a.get("title") or ""
        url = a.get("url") or ""
        lines.append(title)
        if url:
            lines.append(url)
        lines.append("")
    return "\n".join(lines)


def build_world_digest():
    today = datetime.now().strftime("%d.%m.%Y")
    lines = [f"Dunya Gundemi - {today}", ""]
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "domains": WORLD_DOMAINS,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 6,
            "apiKey": NEWSAPI_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    articles = resp.json().get("articles", [])
    if not articles:
        return "Bugun icin dunya gundemi haberi bulunamadi."
    for a in articles:
        title_tr = translate_to_turkish(a.get("title") or "")
        desc_tr = translate_to_turkish((a.get("description") or "")[:400])
        url = a.get("url") or ""
        lines.append(title_tr)
        if desc_tr:
            lines.append(desc_tr)
        if url:
            lines.append(url)
        lines.append("")
    return "\n".join(lines)


def send_telegram(message, chat_id):
    if len(message) > 4000:
        message = message[:3990] + "\n..."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()


def send_menu(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "TR Gundemi", "callback_data": "tr"}],
            [{"text": "Dunya Gundemi", "callback_data": "world"}],
            [{"text": "AI Haberleri", "callback_data": "ai"}],
        ]
    }
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": "Hangi haberleri gormek istersin?",
            "reply_markup": keyboard,
        },
        timeout=15,
    )
    resp.raise_for_status()
