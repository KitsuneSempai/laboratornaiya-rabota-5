""" НАСТРОЙКА ФАЙЛА .ENV
BOT_TOKEN = *************************************
HELP_URL = https://api.mymemory.translated.net/get
LIBRETRANSLATE_URL = https://translate.argosopentech.com/translate
"""
import os
import logging
import requests
import telebot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("LIBRETRANSLATE_URL")
HELP_URL = os.getenv("HELP_URL")

if not BOT_TOKEN or "8881794510:AAEZy" in BOT_TOKEN and "*" in BOT_TOKEN:
    exit("Критическая ошибка: Пожалуйста, укажите реальный BOT_TOKEN в файле .env")

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def translate_text(text: str, target_lang: str) -> str:
    url = HELP_URL
    params = {
        "q": text,
        "langpair": f"Autodetect|{target_lang}"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # MyMemory возвращает статус 200 даже при внутренних ошибках (например, исчерпан лимит)
            if data.get("responseStatus") == 200:
                return data["responseData"]["translatedText"]
            else:
                return f"Ошибка API: {data.get('responseDetails')}"
        else:
            return f"Ошибка API ({response.status_code})"

    except requests.exceptions.RequestException as e:
        return f"Ошибка сети при запросе к API: {e}"


# --- ОБРАБОТЧИКИ КОМАНД TELEGRAM ---

@bot.message_handler(commands=['start'])
def cmd_start(message):
    text = (
        "Привет! Я бот-переводчик.\n"
        "Я использую внешний API для перевода текста.\n\n"
        "Отправь команду в формате:\n"
        "/translate <язык> <текст>\n"
        "Пример: /translate en Привет, мир!\n\n"
        "Для просмотра справки нажми /help"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        "Доступные команды:\n"
        "/start - Приветствие\n"
        "/help - Вызов этой справки\n"
        "/translate <код_языка> <текст> - Перевести текст\n\n"
        "Популярные коды языков:\n"
        "ru - русский\n"
        "en - английский\n"
        "es - испанский\n"
        "de - немецкий\n"
        "fr - французский"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['translate'])
def cmd_translate(message):
    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        bot.send_message(
            message.chat.id,
            "Неверный формат команды!\n"
            "Используй: /translate <код_языка> <текст>\n"
            "Пример: /translate ru Hello"
        )
        return

    target_lang = args[1].lower()
    text_to_translate = args[2]

    processing_msg = bot.send_message(message.chat.id, "🔄 Перевожу...")

    result = translate_text(text_to_translate, target_lang)

    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        text=result
    )


@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """Обработка любого текста без команд"""
    bot.send_message(message.chat.id, "Пожалуйста, используй команду /translate для перевода текста. Подробнее: /help")


# --- ЗАПУСК БОТА ---

if __name__ == "__main__":
    logging.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    try:
        # infinity_polling автоматически обрабатывает падения и переподключается
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\nБот остановлен вручную.")
