import asyncio
import html
import os

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
CHANNEL = os.environ["CHANNEL"]

bot = Bot(TOKEN)
dp = Dispatcher()

HELP = "Пришлите пост, а в двух последних строках кнопки:\nНазвание | https://ссылка"


def build(body_lines, buttons):
    paragraphs = "".join(f"<p>{l}</p>" for l in body_lines if l.strip())
    btns = "".join(
        f'<tg-button type="url" url="{html.escape(u, quote=True)}">{html.escape(t)}</tg-button>'
        for t, u in buttons
    )
    return f"{paragraphs}<tg-button-row>{btns}</tg-button-row>"


@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def publish(m: Message):
    plain = m.text.split("\n")
    rich = m.html_text.split("\n")
    if len(plain) < 3:
        return await m.answer(HELP)
    buttons = [[x.strip() for x in l.rsplit("|", 1)] for l in plain[-2:]]
    if any(len(b) != 2 or not b[1].startswith("https://") for b in buttons):
        return await m.answer(HELP)

    payload = {
        "chat_id": CHANNEL,
        "rich_message": {"html": build(rich[:-2], buttons)},
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://api.telegram.org/bot{TOKEN}/sendRichMessage", json=payload
        ) as r:
            res = await r.json()
    await m.answer("✅ Опубликовано" if res.get("ok") else f"❌ {res.get('description')}")


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
