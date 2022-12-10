import logging
from time import sleep
import telebot
from telebot.types import InputMediaPhoto
from telebot.apihelper import ApiTelegramException
from telebot.util import antiflood

from config import telegram_config, mapbox_config
from app.mongo import db


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

bot = telebot.TeleBot(telegram_config.token_antalya_bot)

chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel


def retry_to_telegram_api(func):
    def wrapper(*args):
        try:
            func(*args)
        except ApiTelegramException as error:
            time_to_sleep = int(error.result_json['parameters']['retry_after'])
            sleep(time_to_sleep + 1)
            func(*args)
    return wrapper


def get_map_image(ad):
    if not ad.lat or not ad.lon:
        return None
    url = f"{mapbox_config.url}/pin-l+0031f5({ad.lon},{ad.lat})/{ad.lon},{ad.lat},12/1200x600?access_token={mapbox_config.token}"
    return url


def make_caption(ad, status='new'):
    first_price = f"{ad.first_price:,.0f}".replace(',', ' ')
    last_price = f"{ad.last_price:,.0f}".replace(',', ' ')
    date = ad.last_price_update.strftime('%d.%m.%Y')
    link = ad.short_url
    if status == 'new':
        caption = '<a href="{}">{}</a>\n{} TL / {}'
        return caption.format(link, ad.title, last_price, date)
    if status == 'update':
        caption = '<a href="{}">{}</a>\n<s>{} TL</s> {} TL / {}'
        return caption.format(link, ad.title, first_price, last_price, date)
    elif status == 'remove':
        caption = '<a href="{}">{}</a>\n<b>{}</b> / {}'
        return caption.format(link, ad.title, 'Ad removed', date)


def send_comment_for_ad_to_telegram(ad):
    telegram_chat_message_id = ad.telegram_chat_message_id

    if not telegram_chat_message_id:
        return
    format_new_price = f"{ad.last_price:,.0f}".replace(',', ' ')
    price_diff = ad.last_price - ad.history_price[-2].price
    format_price_diff = f"{price_diff}".replace(',', ' ')
    icon = '📉 ' if price_diff < 0 else '📈 +'
    comment = '{}{} TL = {} TL'
    format_comment = comment.format(icon, format_price_diff, format_new_price)
    antiflood(
        bot.send_message,
        chat_id=chat_id,
        text=format_comment,
        reply_to_message_id=telegram_chat_message_id,
        parse_mode='HTML'
    )


def edit_ad_in_telegram(ad, status):
    telegram_channel_message_id = ad.telegram_channel_message_id

    if not telegram_channel_message_id:
        return
    caption = make_caption(ad, status)
    kw = dict(chat_id=channel_id, message_id=telegram_channel_message_id, parse_mode='HTML')
    if ad.thumbnail_url:
        antiflood(bot.edit_message_caption, caption=caption, **kw)
    else:
        antiflood(bot.edit_message_text, text=caption, **kw)


def send_ad_to_telegram(ad):
    media = [InputMediaPhoto(media=get_map_image(ad), caption=make_caption(ad), parse_mode='HTML')]
    for photo in ad.photos:
        media.append(InputMediaPhoto(media=photo))
    antiflood(bot.send_media_group, chat_id=channel_id, media=media)


@bot.message_handler(content_types=['photo'])
@bot.message_handler(func=lambda message: True)
def get_telegram_message_id(message):
    telegram_chat_message_id = message.message_id
    if message.forward_from_chat and message.forward_from_chat.id == int(channel_id):
        telegram_channel_message_id = message.forward_from_message_id
        try:
            if message.content_type == 'photo':
                if 'caption_entities' not in message.json:
                    return
                url = message.json['caption_entities'][0]['url']
            else:
                url = message.json['entities'][0]['url']
        except Exception as e:
            logging.error(e)
            url = None
        if not url:
            return
        id = url.replace('https://www.sahibinden.com/', '')
        ad = db.flats.find_one({'_id': id})
        if not ad:
            logging.info('Ad not found')
            return
        ad['telegram_channel_message_id'] = telegram_channel_message_id
        ad['telegram_chat_message_id'] = telegram_chat_message_id
        db.flats.find_one_and_replace({'_id': ad['_id']}, ad)


def telegram_notify(ad):
    if ad.removed:
        edit_ad_in_telegram(ad, 'remove')
    elif ad.last_seen == ad.created:
        send_ad_to_telegram(ad)
    elif ad.last_seen == ad.last_update:
        send_comment_for_ad_to_telegram(ad)
        edit_ad_in_telegram(ad, 'update')
    elif ad.last_condition_removed:
        if len(ad.history_price) == 1:
            edit_ad_in_telegram(ad, 'new')
        else:
            edit_ad_in_telegram(ad, 'update')


if __name__ == '__main__':
    bot.infinity_polling()
