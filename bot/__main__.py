from telegram.ext import Updater

from config import telegram_config

from bot.conversation import setup_conversation
from bot.get_id import setup_get_id

updater = Updater(telegram_config.token_antalya_bot)

chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel


def main() -> None:
    dispatcher = updater.dispatcher
    setup_conversation(dispatcher)
    setup_get_id(dispatcher)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
