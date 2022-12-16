import logging

import telebot

from config import telegram_config
from mongo import db
from telegram.models import TelegramIdAd


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

bot = telebot.TeleBot(telegram_config.token_antalya_bot)

chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel


@bot.message_handler(content_types=["photo"])
@bot.message_handler(func=lambda message: True)
def get_telegram_message_id(message: telebot.types.Message) -> None:
    telegram_chat_message_id = message.message_id
    if message.forward_from_chat and message.forward_from_chat.id == int(channel_id):
        telegram_channel_message_id = message.forward_from_message_id
        try:
            if message.content_type == "photo":
                if "caption_entities" not in message.json:
                    return
                url = message.json["caption_entities"][0]["url"]
            else:
                url = message.json["entities"][0]["url"]
        except Exception as e:
            logging.error(e)
            url = None
        if not url:
            return
        id = url.replace("https://www.sahibinden.com/", "")

        post = TelegramIdAd(
            telegram_chat_message_id=telegram_chat_message_id,
            telegram_channel_message_id=telegram_channel_message_id,
            _id=id,
        )
        db.telegram_posts.find_one_and_replace({"_id": id}, post.dict(by_alias=True), upsert=True)

        ad = db.flats.find_one({"_id": id})
        if not ad:
            logging.info("Ad not found")
            return
        ad["telegram_channel_message_id"] = telegram_channel_message_id
        ad["telegram_chat_message_id"] = telegram_chat_message_id
        db.flats.find_one_and_replace({"_id": ad["_id"]}, ad)
