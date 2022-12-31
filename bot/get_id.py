import logging

from telegram import Update
from telegram.ext import MessageHandler, CallbackContext, filters, Application

from bot.models import TelegramIdAd
from mongo import db
from config import telegram_config

chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


async def get_telegram_message_id(update: Update, context: CallbackContext) -> None:
    telegram_chat_message_id = update.message.message_id
    telegram_channel_message_id = update.message.forward_from_message_id
    url = update.message.caption_entities[0].url
    ad_id = url.replace("https://www.sahibinden.com/", "")

    post = TelegramIdAd(
        telegram_chat_message_id=telegram_chat_message_id,
        telegram_channel_message_id=telegram_channel_message_id,
        _id=ad_id,
    )
    db.telegram_posts.find_one_and_replace({"_id": ad_id}, post.dict(by_alias=True), upsert=True)


def setup_get_id(application: Application) -> None:
    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.CaptionEntity('text_link') & filters.ForwardedFrom(chat_id=int(channel_id)),
            get_telegram_message_id
        )
    )
