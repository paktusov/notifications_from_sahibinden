import logging

import telebot

from config import telegram_config
from mongo import db
from telegram.models import TelegramIdAd

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

bot = telebot.TeleBot(telegram_config.token_antalya_bot)

chat_id = telegram_config.id_antalya_chat
subscribers = {}
channel_id = telegram_config.id_antalya_channel


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    subscribers[message.chat.id] = {}
    bot.reply_to(message, "Привет, ищешь квартиру в Антилии? Укажи ценовой диапазон в TL и я буду присылать тебе объявления")


@bot.message_handler(func=lambda message: True)
def get_user_max_price(message):
    try:
        max_price = int(message.text)
        db.subscribers.find_one_and_replace(
            {"_id": message.chat.id},
            dict(_id=message.chat.id, max_price=max_price),
            upsert=True,
        )
        bot.reply_to(message, f"Я буду присылать тебе объявления до {max_price} TL")
    except ValueError:
        bot.reply_to(message, "Цена должна быть числом")
        return
    except Exception as e:
        logger.error(e)
        bot.reply_to(message, "Что-то пошло не так")
        return


@bot.message_handler(content_types=["photo"])
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
        except KeyError as e:
            logging.error(e)
            return
        ad_id = url.replace("https://www.sahibinden.com/", "")

        post = TelegramIdAd(
            telegram_chat_message_id=telegram_chat_message_id,
            telegram_channel_message_id=telegram_channel_message_id,
            _id=ad_id,
        )
        db.telegram_posts.find_one_and_replace({"_id": ad_id}, post.dict(by_alias=True), upsert=True)
