import telebot

from notifications_from_sahibinden.config import telegram_config


def send_ad_to_telegram(ad):
    bot = telebot.TeleBot(telegram_config.token_antalya)
    chat_id = telegram_config.id_antalya
    last_price = ad['history_price'][-1][0]
    link = 'https://www.sahibinden.com' + ad['url']
    caption = '<a href="{}">{}</a>\n\n{} L.'
    format_caption = caption.format(link,
                                    ad['title'],
                                    last_price,
                                    )
    if ad['thumbnailUrl']:
        bot.send_photo(chat_id=chat_id, photo=ad['thumbnailUrl'], caption=format_caption, parse_mode='HTML')
    else:
        bot.send_message(chat_id=chat_id, text=format_caption, parse_mode='HTML')