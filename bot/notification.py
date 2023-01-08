import logging

from telegram import InputMediaPhoto
from telegram.error import TelegramError

from bot.bot import application
from bot.models import TelegramIdAd
from config import telegram_config
from mongo import db

from app.models import Ad


chat_id = telegram_config.id_antalya_chat
channel_id = telegram_config.id_antalya_channel

logger = logging.getLogger(__name__)

closed_ares = [area["name"] for area in db.areas.find({"is_closed": True})]
connection_parameters = dict(connect_timeout=20, read_timeout=20)


def subscription_validation(ad: Ad, parameters: dict) -> bool:
    if parameters.get("max_price") and ad.last_price > parameters["max_price"]:
        return False

    if parameters.get("floor"):
        if "without_last" in parameters["floor"] and ad.data.floor == str(ad.data.building_floor_count):
            return False
        if "without_first" in parameters["floor"] and ad.data.floor in ["Elevation 1", "Garden-Floor"]:
            return False
        if "without_basement" in parameters["floor"] and ad.data.floor in [
            "Basement",
            "Ground Floor",
            "Raised Ground Floor",
        ]:
            return False

    if parameters.get("rooms"):
        suitable_rooms = False
        if "studio" in parameters["rooms"] and ad.data.room_count == "Studio Flat (1+0)":
            suitable_rooms = True
        if "one" in parameters["rooms"] and ad.data.room_count in ["1+1", "1.5+1"]:
            suitable_rooms = True
        if "two" in parameters["rooms"] and ad.data.room_count in ["2+0", "2+1", "2.5+1", "2+2"]:
            suitable_rooms = True
        if "three" in parameters["rooms"] and ad.data.room_count in ["3+0", "3+1", "3.5+1", "3+2", "3+3"]:
            suitable_rooms = True
        if "four" in parameters["rooms"] and ad.data.room_count in [
            "4+0",
            "4+1",
            "4.5+1",
            "4+2",
            "4+3",
            "4+4",
            "5+1",
            "5.5+1",
            "5+2",
            "5+3",
            "5+4",
            "6+1",
            "6+2",
            "6+3",
            "6+4",
            "7+1",
            "7+2",
            "7+3",
            "8+1",
            "8+2",
            "8+3",
            "8+4",
            "9+1",
            "9+2",
            "9+3",
            "9+4",
            "9+5",
            "9+6",
            "10+1",
            "10+2",
            "Over 10",
        ]:
            suitable_rooms = True
        if not suitable_rooms:
            return False
    if parameters.get("heating"):
        suitable_heating = False
        if "gas" in parameters["heating"] and ad.data.heating_type == "Central Heating Boilers":
            suitable_heating = True
        if "electricity" in parameters["heating"] and ad.data.heating_type in ["Elektrikli Radyatör", "Room Heater"]:
            suitable_heating = True
        if "central" in parameters["heating"] and ad.data.heating_type in [
            "Central Heating",
            "Central Heating (Share Meter)",
        ]:
            suitable_heating = True
        if "underfloor" in parameters["heating"] and ad.data.heating_type == "Floor Heating":
            suitable_heating = True
        if "ac" in parameters["heating"] and ad.data.heating_type in [
            "Air Conditioning",
            "Fan Coil Unit",
            "VRV",
            "Heat Pump",
        ]:
            suitable_heating = True
        if not suitable_heating:
            return False

    return True


def format_price(price: float) -> str:
    return f"{price:,.0f}".replace(",", " ")


def make_caption(ad: Ad, status: str = "new") -> str:
    first_price = format_price(ad.first_price)
    last_price = format_price(ad.last_price)
    date = ad.last_price_update.strftime("%d.%m.%Y")
    hiperlink = f'<a href="{ad.short_url}">{ad.title}</a>\n'
    if status == "new":
        price = f"{last_price} TL\n"
    elif status == "update":
        price = f"<s>{first_price} TL</s> {last_price} TL on {date}\n"
    else:
        price = f"<s>{first_price} TL</s> Ad removed on {date}\n"
    if not ad.data:
        caption = hiperlink + price
        return caption
    if ad.data.area in closed_ares:
        ad.data.area += "⛔️"
    location = f"#{ad.data.district} / #{ad.data.area}\n"
    rooms = f"{ad.data.room_count}\n"
    area = f"{ad.data.net_area} ({ad.data.gross_area}) m²\n"
    floor = f"{ad.data.floor}/{ad.data.building_floor_count} floor\n"
    age = f"{ad.data.building_age} y.o\n"
    heating = f"{ad.data.heating_type}\n"
    furniture = "Furniture" if ad.data.furniture else "No furniture"
    caption = hiperlink + price + location + rooms + area + floor + age + heating + furniture
    return caption


async def send_comment_for_ad_to_telegram(ad: Ad) -> None:
    telegram_post_dict = db.telegram_posts.find_one({"_id": ad.id})
    if not telegram_post_dict:
        logging.error("Telegram post not found for ad %s", ad.id)
        return
    telegram_post = TelegramIdAd(**telegram_post_dict)
    telegram_chat_message_id = telegram_post.telegram_chat_message_id
    new_price = format_price(ad.last_price)
    price_diff = ad.last_price - ad.history_price[-2].price
    formatted_price_diff = format_price(ad.last_price - ad.history_price[-2].price)
    icon = "📉 " if price_diff < 0 else "📈 +"
    comment = f"{icon}{formatted_price_diff} TL = {new_price} TL"
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=comment,
            reply_to_message_id=telegram_chat_message_id,
            parse_mode="HTML",
            **connection_parameters,
        )
        logging.info("Comment ad %s to telegram", ad.id)
    except TelegramError as e:
        logging.error("Error while sending comment for ad %s to telegram: %s", ad.id, e)


async def edit_ad_in_telegram(ad: Ad, status: str) -> None:
    telegram_post_dict = db.telegram_posts.find_one({"_id": ad.id})
    if not telegram_post_dict:
        logging.error("Telegram post not found for ad %s", ad.id)
        return
    telegram_post = TelegramIdAd(**telegram_post_dict)
    telegram_channel_message_id = telegram_post.telegram_channel_message_id
    caption = make_caption(ad, status)
    try:
        await application.bot.edit_message_caption(
            chat_id=channel_id,
            message_id=telegram_channel_message_id,
            parse_mode="HTML",
            caption=caption,
            **connection_parameters,
        )
        logging.info("Edit ad %s to telegram", ad.id)
    except TelegramError as e:
        logging.error("Error while editing ad %s in telegram: %s", ad.id, e)


async def send_ad_to_telegram(ad: Ad) -> None:
    media = [InputMediaPhoto(media=ad.map_image, caption=make_caption(ad), parse_mode="HTML")]
    for photo in ad.photos:
        media.append(InputMediaPhoto(media=photo))
    try:
        await application.bot.send_media_group(chat_id=channel_id, media=media, **connection_parameters)
        logging.info("Sending ad %s to telegram", ad.id)
        subscribers = db.subscribers.find({"active": True})
        for subscriber in subscribers:
            parameters = subscriber["parameters"]
            if not subscription_validation(ad, parameters):
                continue
            await application.bot.send_media_group(chat_id=subscriber["_id"], media=media, **connection_parameters)
            logging.info("Send message %s to %s", ad.id, subscriber["_id"])
    except TelegramError as e:
        logging.error("Error while sending ad %s to telegram: %s", ad.id, e)


async def telegram_notify(ad: Ad) -> None:
    if ad.removed:
        await edit_ad_in_telegram(ad, "remove")
    elif ad.last_seen == ad.created and ad.data and (ad.created - ad.data.creation_date).days < 1:
        await send_ad_to_telegram(ad)
    elif ad.last_seen == ad.last_update:
        await send_comment_for_ad_to_telegram(ad)
        await edit_ad_in_telegram(ad, "update")
    elif ad.last_condition_removed:
        if len(ad.history_price) == 1:
            await edit_ad_in_telegram(ad, "new")
        else:
            await edit_ad_in_telegram(ad, "update")
