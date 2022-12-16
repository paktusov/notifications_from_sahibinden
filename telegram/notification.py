from telebot.types import InputMediaPhoto
from telebot.util import antiflood

from telegram.bot import bot, channel_id, chat_id

from app.models import Ad


def make_caption(ad: Ad, status: str = "new") -> str:
    first_price = f"{ad.first_price:,.0f}".replace(",", " ")
    last_price = f"{ad.last_price:,.0f}".replace(",", " ")
    date = ad.last_price_update.strftime("%d.%m.%Y")
    hiperlink = f'<a href="{ad.short_url}">{ad.title}</a>\n'
    if status == "new":
        price = f"{last_price} TL on {date}\n"
    elif status == "update":
        price = f"<s>{first_price} TL</s> {last_price} TL on {date}\n"
    else:
        price = f"<s>{first_price} TL</s> Ad removed on {date}\n"
    if not ad.data:
        caption = hiperlink + price
        return caption
    location = f"{ad.data.district} / {ad.data.area}\n"
    rooms = f"{ad.data.room_count}\n"
    area = f"{ad.data.net_area} ({ad.data.gross_area}) m²\n"
    floor = f"{ad.data.floor}/{ad.data.building_floor_count} floor\n"
    age = f"{ad.data.building_age} y.o\n"
    heating = f"{ad.data.heating_type}\n"
    furniture = "Furniture" if ad.data.furniture else "No furniture"
    caption = hiperlink + price + location + rooms + area + floor + age + heating + furniture
    return caption


def send_comment_for_ad_to_telegram(ad: Ad) -> None:
    telegram_chat_message_id = ad.telegram_chat_message_id

    if not telegram_chat_message_id:
        return
    format_new_price = f"{ad.last_price:,.0f}".replace(",", " ")
    price_diff = ad.last_price - ad.history_price[-2].price
    format_price_diff = f"{price_diff}".replace(",", " ")
    icon = "📉 " if price_diff < 0 else "📈 +"
    comment = f"{icon}{format_price_diff} TL = {format_new_price} TL"
    format_comment = comment.format(icon, format_price_diff, format_new_price)
    antiflood(
        bot.send_message,
        chat_id=chat_id,
        text=format_comment,
        reply_to_message_id=telegram_chat_message_id,
        parse_mode="HTML",
    )


def edit_ad_in_telegram(ad: Ad, status: str) -> None:
    telegram_channel_message_id = ad.telegram_channel_message_id

    if not telegram_channel_message_id:
        return
    caption = make_caption(ad, status)
    kw = dict(chat_id=channel_id, message_id=telegram_channel_message_id, parse_mode="HTML")
    if ad.thumbnail_url:
        antiflood(bot.edit_message_caption, caption=caption, **kw)
    else:
        antiflood(bot.edit_message_text, text=caption, **kw)


def send_ad_to_telegram(ad: Ad) -> None:
    media = [InputMediaPhoto(media=ad.map_image, caption=make_caption(ad), parse_mode="HTML")]
    for photo in ad.photos:
        media.append(InputMediaPhoto(media=photo))
    antiflood(bot.send_media_group, chat_id=channel_id, media=media)


def telegram_notify(ad: Ad) -> None:
    if ad.removed:
        edit_ad_in_telegram(ad, "remove")
    elif ad.last_seen == ad.created:
        send_ad_to_telegram(ad)
    elif ad.last_seen == ad.last_update:
        send_comment_for_ad_to_telegram(ad)
        edit_ad_in_telegram(ad, "update")
    elif ad.last_condition_removed:
        if len(ad.history_price) == 1:
            edit_ad_in_telegram(ad, "new")
        else:
            edit_ad_in_telegram(ad, "update")
