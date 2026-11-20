import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

ADMIN_ID = int(os.environ["ADMIN_ID"])
CHANNEL = os.environ["CHANNEL"]

bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

HELP = "Пришлите пост, а в двух последних строках кнопки:\nНазвание | https://ссылка"


@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def publish(m: Message):
    plain = m.text.split("\n")
    html = m.html_text.split("\n")
    if len(plain) < 3:
        return await m.answer(HELP)
    try:
        rows = []
        for line in plain[-2:]:
            title, url = line.rsplit("|", 1)
            rows.append([InlineKeyboardButton(text=title.strip(), url=url.strip())])
        await bot.send_message(
            CHANNEL,
            "\n".join(html[:-2]),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        await m.answer("✅ Опубликовано")
    except Exception as e:
        await m.answer(f"❌ {e}\n\n{HELP}")


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
