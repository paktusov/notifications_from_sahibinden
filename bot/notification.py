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


def check_floor(ad: Ad, parameter: list[str]) -> bool:
    if "without_last" in parameter and ad.data.floor == str(ad.data.building_floor_count):
        return False
    if "without_first" in parameter and ad.data.floor in ["Elevation 1", "Garden-Floor"]:
        return False
    if "without_basement" in parameter and ad.data.floor in ["Basement", "Ground Floor", "Raised Ground Floor"]:
        return False
    return True


def check_rooms(ad: Ad, parameter: list[str]) -> bool:
    if "studio" in parameter and ad.data.room_count == "Studio Flat (1+0)":
        return True
    rooms, *_ = ad.data.room_count.split("+")
    if "one" in parameter and rooms in ["1", "1.5"]:
        return True
    if "two" in parameter and rooms in ["2", "2.5"]:
        return True
    if "three" in parameter and rooms in ["3", "3.5+1"]:
        return True
    if "four" in parameter and rooms in ["4", "4.5", "5", "5.5", "6", "7", "8", "9", "10", "Over 10"]:
        return True
    return False


def check_heating(ad: Ad, parameter: list[str]) -> bool:
    if "gas" in parameter and ad.data.heating_type == "Central Heating Boilers":
        return True
    if "electricity" in parameter and ad.data.heating_type in ["Elektrikli Radyatör", "Room Heater"]:
        return True
    if "central" in parameter and ad.data.heating_type in ["Central Heating", "Central Heating (Share Meter)"]:
        return True
    if "underfloor" in parameter and ad.data.heating_type == "Floor Heating":
        return True
    if "ac" in parameter and ad.data.heating_type in ["Air Conditioning", "Fan Coil Unit", "VRV", "Heat Pump"]:
        return True
    return False


def check_furniture(ad: Ad, parameter: list) -> bool:
    if ad.data.furniture and "furnished" not in parameter:
        return False
    if not ad.data.furniture and "unfurnished" not in parameter:
        return False
    return True


def check_area(ad: Ad, parameter: dict) -> bool:
    if bool(parameter['all_' + ad.address_town]):
        return True
    if parameter[ad.data.area]:
        return True
    return False


def subscription_validation(ad: Ad, parameters: dict) -> bool:
    if not ad.data:
        return False
    if parameters.get("max_price") and ad.last_price > int(parameters["max_price"][0]):
        return False
    if parameters.get("floor"):
        return check_floor(ad, parameters["floor"])
    if parameters.get("rooms"):
        return check_rooms(ad, parameters["rooms"])
    if parameters.get("heating"):
        return check_heating(ad, parameters["heating"])
    if parameters.get("furniture"):
        return check_furniture(ad, parameters["furniture"])
    if parameters.get("area"):
        return check_area(ad, parameters["area"])
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
