import telegram
from logzero import logger

import settings


class TelegramBot:
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN):
        self.bot = telegram.Bot(token)

    def send(self, chat_id: str, text: str):
        logger.debug(f'📤 Sending message to chat id {chat_id} through Telegram Bot')
        self.bot.send_message(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
