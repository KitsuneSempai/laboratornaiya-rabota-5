import asyncio
import logging
import os
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject

# =====================================================================
# CONFIGURATION & LOGGING
# =====================================================================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN в файле .env")
bot = Bot(token=TOKEN)
dp = Dispatcher()
# =====================================================================
# API SERVICE LOGIC (Функция работы с переводчиком)
# =====================================================================
async def translate_text(target_lang: str, text: str) -> str:
    url = os.getenv("LIBRETRANSLATE_URL", "https://translate.argosopentech.com/translate")
    api_key = os.getenv("LIBRETRANSLATE_API_KEY", "")
    payload = {
        "q": text,
        "source": "auto",  # Автоматическое определение языка
        "target": target_lang,
        "format": "text",
        "api_key": api_key
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("translatedText", "Ошибка: пустой ответ от сервера.")
                elif response.status == 400:
                    return "Ошибка 400: Неверно указан язык или некорректный запрос."
                elif response.status == 429:
                    return "Ошибка 429: Слишком много запросов. Попробуйте позже."
                else:
                    return f"Ошибка API: {response.status}."
    except aiohttp.ClientError as e:
        logger.error(f"Сетевая ошибка при обращении к API: {e}")
        return "Проблема с сетью: API переводчика временно недоступно."
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        return "Произошла непредвиденная ошибка при обработке перевода."

# =====================================================================
# TELEGRAM BOT HANDLERS (Обработчики команд)
# =====================================================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 Привет! Я бот-переводчик.\n\n"
        "Я могу переводить текст на разные языки с помощью LibreTranslate.\n"
        "Отправь /help, чтобы узнать, как мной пользоваться."
    )
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📖 **Справка по использованию:**\n\n"
        "Чтобы перевести текст, используйте команду `/translate`.\n\n"
        "**Формат:**\n"
        "`/translate <код_языка> <текст>`\n\n"
        "**Примеры:**\n"
        "`/translate en Привет, мир!` — переведет на английский.\n"
        "`/translate fr Доброе утро` — переведет на французский."
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("translate"))
async def cmd_translate(message: types.Message, command: CommandObject):
    if command.args is None:
        await message.answer("Ошибка: Вы не ввели аргументы.\nИспользуйте формат: `/translate en Привет!`", parse_mode="Markdown")
        return
    args_split = command.args.split(" ", maxsplit=1)
    if len(args_split) < 2:
        await message.answer("Ошибка: Недостаточно аргументов.\nИспользуйте формат: `/translate <язык> <текст>`", parse_mode="Markdown")
        return
    target_lang = args_split[0]
    text_to_translate = args_split[1]
    wait_message = await message.answer("⏳ Перевожу...")
    # Вызываем функцию, которая теперь находится в этом же файле
    translated_result = await translate_text(target_lang, text_to_translate)

    await wait_message.edit_text(f"**Перевод:**\n{translated_result}", parse_mode="Markdown")

# =====================================================================
# MAIN RUNNER
# =====================================================================
async def main():
    print("Бот запущен из одного файла...")
    await dp.start_polling(bot)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")