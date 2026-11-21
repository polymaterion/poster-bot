import asyncio
import html
import os
import re

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
CHANNEL = os.environ["CHANNEL"]

MAX_IN_ROW, MAX_ROWS = 3, 15
STYLES = {"🟥": "danger", "🟩": "success", "🟦": "primary"}

PART = re.compile(
    r'^(?P<color>[🟥🟩🟦])?\s*'
    r'(?:<tg-emoji emoji-id="(?P<emoji>\d+)">(?P<alt>[^<]*)</tg-emoji>)?\s*'
    r'(?P<title>.+?)\s+[-–—]\s+(?P<url>(?:https?|tg)://\S+)$'
)

HELP = (
    "Пришлите пост, а под ним кнопки:\n\n"
    "Кнопка 1 - https://example1.com\n"
    "Кнопка 2 - https://example2.com | Кнопка 3 - https://example3.com\n\n"
    "🟥 🟩 🟦 в начале строки задают цвет, эмодзи после цвета добавляется в кнопку.\n"
    "Не больше 3 кнопок в ряд и 15 рядов."
)

bot = Bot(TOKEN)
dp = Dispatcher()


def parse_row(line):
    matches = [PART.match(p.strip()) for p in line.split("|")]
    if not all(matches):
        return None
    return [mt.groupdict() for mt in matches]


def split_message(lines):
    rows = []
    while lines:
        if not lines[-1].strip():
            lines.pop()
            continue
        row = parse_row(lines[-1])
        if row is None:
            break
        rows.insert(0, row)
        lines.pop()
    return lines, rows


def render_button(b):
    title = html.unescape(re.sub(r"<[^>]+>", "", b["title"]))
    url = html.unescape(b["url"])
    style = STYLES.get(b["color"])
    style_attr = f' style="{style}"' if style else ""
    emoji = ""
    if b["emoji"]:
        emoji = f'<tg-emoji emoji-id="{b["emoji"]}">{html.escape(b["alt"])}</tg-emoji> '
    return (
        f'<tg-button type="url" url="{html.escape(url, quote=True)}"{style_attr}>'
        f"{emoji}{html.escape(title)}</tg-button>"
    )


@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def publish(m: Message):
    body, rows = split_message(m.html_text.split("\n"))
    body = [l for l in body if l.strip()]
    if not body or not rows:
        return await m.answer(HELP)
    if len(rows) > MAX_ROWS or any(len(r) > MAX_IN_ROW for r in rows):
        return await m.answer(f"Максимум {MAX_IN_ROW} кнопки в ряд и {MAX_ROWS} рядов.")

    markup = "".join(f"<p>{l}</p>" for l in body) + "".join(
        "<tg-button-row>" + "".join(render_button(b) for b in row) + "</tg-button-row>"
        for row in rows
    )
    payload = {"chat_id": CHANNEL, "rich_message": {"html": markup}}
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://api.telegram.org/bot{TOKEN}/sendRichMessage", json=payload
        ) as r:
            res = await r.json()
    await m.answer("✅ Опубликовано" if res.get("ok") else f"❌ {res.get('description')}")


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
