import logging
import telebot

from config import telegram_config
from notifications_from_sahibinden.mongo import get_db


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

bot = telebot.TeleBot(telegram_config.token_antalya)

chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel


def make_caption(ad):
    last_price = f"{ad['history_price'][-1][0]:,.0f}".replace(',', ' ')
    dt = ad['history_price'][-1][1].strftime('%d.%m.%Y %H:%M')
    link = 'https://www.sahibinden.com' + ad['url']
    caption = '<a href="{}">{}</a>\n{} TL / {}'
    format_caption = caption.format(link, ad['title'], last_price, dt)
    return format_caption


def send_comment_for_ad_to_telegram(ad):
    telegram_chat_message_id = ad.get('telegram_chat_message_id')
    telegram_channel_message_id = ad.get('telegram_channel_message_id')

    if telegram_chat_message_id:
        format_new_price = f"{ad['history_price'][-1][0]:,.0f}".replace(',', ' ')
        price_diff = ad['history_price'][-1][0] - ad['history_price'][-2][0]
        format_price_diff = f"{price_diff}".replace(',', ' ')
        if price_diff < 0:
            icon = '📉 '
        else:
            icon = '📈 +'
        comment = '{}{} TL = {} TL'
        format_comment = comment.format(icon, format_price_diff, format_new_price)
        bot.send_message(chat_id=chat_id, text=format_comment, reply_to_message_id=telegram_chat_message_id, parse_mode='HTML')

    if telegram_channel_message_id:
        caption = make_caption(ad)
        if ad['thumbnailUrl']:
            bot.edit_message_caption(
                chat_id=channel_id,
                message_id=telegram_channel_message_id,
                caption=caption,
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                chat_id=channel_id,
                message_id=telegram_channel_message_id,
                text=caption,
                parse_mode='HTML'
            )


def send_ad_to_telegram(ad):
    caption = make_caption(ad)
    if ad['thumbnailUrl']:
        bot.send_photo(chat_id=channel_id, photo=ad['thumbnailUrl'], caption=caption, parse_mode='HTML')
    else:
        bot.send_message(chat_id=channel_id, text=caption, parse_mode='HTML')


@bot.message_handler(content_types=['photo'])
@bot.message_handler(func=lambda message: True)
def record_ad_message_photo_id(message):
    telegram_chat_message_id = message.message_id
    if message.forward_from_chat and message.forward_from_chat.id == int(channel_id) and message.from_user.id == 777000:
        telegram_channel_message_id = message.forward_from_message_id
        if message.content_type == 'photo':
            title = message.caption
        else:
            title = message.text
        ad = get_db().flats.find_one({'title': title.split('\n')[0]})
        if ad:
            ad['telegram_channel_message_id'] = telegram_channel_message_id
            ad['telegram_chat_message_id'] = telegram_chat_message_id
            get_db().flats.find_one_and_replace({'_id': ad['_id']}, ad)


if __name__ == '__main__':
    bot.infinity_polling()
