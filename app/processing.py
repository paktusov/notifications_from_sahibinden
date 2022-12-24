import logging
from datetime import datetime

from mongo import db
from telegram.notification import telegram_notify

from app.get_data import get_data_and_photos_ad, get_data_with_cookies, get_map_image, get_areas
from app.models import Ad, DataAd, Area


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)




def create_dataad_from_data(data: dict) -> DataAd:
    return DataAd(
        region=data.get("loc2"),
        district=data.get("loc3"),
        area=data.get("loc5"),
        creation_date=datetime.strptime(data.get("Ad Date"), "%d %B %Y"),
        gross_area=data.get("m² (Brüt)"),
        net_area=data.get("m² (Net)"),
        room_count=data.get("Oda Sayısı"),
        building_age=data.get("Bina Yaşı"),
        floor=data.get("Bulunduğu Kat"),
        building_floor_count=int(data.get("Kat Sayısı")),
        heating_type=data.get("Isıtma"),
        bathroom_count=data.get("Banyo Sayısı"),
        balcony=bool(data.get("Balkon")),
        furniture=bool(data.get("Eşyalı") == "Yes"),
        using_status=data.get("Kullanım Durumu"),
        dues=data.get("Aidat (TL)"),
        deposit=data.get("Depozito (TL)"),
    )


def create_ad_from_data(data: list[dict]) -> list[Ad]:
    return [Ad(**row) for row in data if not (int(row["id"]) < 1000000000 and not row["thumbnailUrl"])]


def processing_data(city_parameter: dict) -> None:
    flats = db.flats
    now_time = datetime.now()
    data = get_data_with_cookies(city_parameter)
    if not data:
        logger.warning("Can't parse ads from sahibinden.com")
        return
    parsed_ads = create_ad_from_data(data)

    ids = [ad.id for ad in parsed_ads]

    existed_ads = {ad["_id"]: Ad(**ad) for ad in flats.find({"_id": {"$in": ids}})}

    for ad in parsed_ads:
        if ad.id in existed_ads:
            ad.update_from_existed(existed_ads[ad.id])
        else:
            dataad, photos = get_data_and_photos_ad(ad.full_url)
            if dataad:
                ad.data = create_dataad_from_data(dataad)
            else:
                logger.error("Can't parse ad data from %s", ad.id)
            if not photos:
                logger.error("Can't parse ad photos from %s", ad.id)
            ad.photos = photos

            map_image = get_map_image(ad.lat, ad.lon)
            if not map_image:
                logger.error("Can't parse ad map image from %s", ad.id)
            ad.map_image = map_image

        flats.find_one_and_replace({"_id": ad.id}, ad.dict(by_alias=True), upsert=True)
        telegram_notify(ad)

    missed_ad = [Ad(**ad) for ad in flats.find({"last_seen": {"$lt": now_time}, "removed": False})]

    for ad in missed_ad:
        ad.remove()
        flats.find_one_and_replace({"_id": ad.id}, ad.dict(by_alias=True), upsert=True)
        telegram_notify(ad)
