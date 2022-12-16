from datetime import datetime

from mongo import db, get_db
from telegram.notification import telegram_notify

from app.get_data import get_ad_photos, get_data_ad, get_data_with_cookies, get_map_image
from app.models import Ad, DataAd


def create_dataad_from_data(data: dict) -> DataAd:
    return DataAd(
        region=data.get("loc2"),
        district=data.get("loc3"),
        area=data.get("loc5"),
        creation_date=datetime.strptime(data.get("Ad Date"), "%d %B %Y"),
        gross_area=int(data.get("m² (Brüt)")),
        net_area=int(data.get("m² (Net)")),
        room_count=data.get("Oda Sayısı"),
        building_age=data.get("Bina Yaşı"),
        floor=data.get("Bulunduğu Kat"),
        building_floor_count=int(data.get("Kat Sayısı")),
        heating_type=data.get("Isıtma"),
        bathroom_count=data.get("Banyo Sayısı"),
        balcony=bool(data.get("Balkon")),
        furniture=True if data.get("Eşyalı") == "Yes" else False,
        using_status=data.get("Kullanım Durumu"),
        dues=data.get("Aidat (TL)"),
        deposit=data.get("Depozito (TL)"),
    )


def create_ad_from_data(data: list[dict]) -> list[Ad]:
    return [
        Ad(**row) for row in data["classifiedMarkers"] if not (int(row["id"]) < 1000000000 and not row["thumbnailUrl"])
    ]


def processing_data():
    flats = get_db().flats
    now_time = datetime.now()

    parsed_ads = create_ad_from_data(get_data_with_cookies())

    ids = [ad.id for ad in parsed_ads]

    existed_ads = {ad["_id"]: Ad(**ad) for ad in flats.find({"_id": {"$in": ids}})}

    for ad in parsed_ads:
        if ad.id in existed_ads:
            ad.update_from_existed(existed_ads[ad.id])
        else:
            ad.data = create_dataad_from_data(get_data_ad(ad.full_url))
            ad.photos = get_ad_photos(ad.full_url)
            ad.map_image = get_map_image(ad.lat, ad.lon)
        db.flats.find_one_and_replace({"_id": ad.id}, ad.dict(by_alias=True), upsert=True)
        # logging.info(f'Ad {ad.id} saved')
        telegram_notify(ad)

    missed_ad = [Ad(**ad) for ad in flats.find({"last_seen": {"$lt": now_time}, "removed": False})]

    for ad in missed_ad:
        ad.remove()
        db.flats.find_one_and_replace({"_id": ad.id}, ad.dict(by_alias=True), upsert=True)
        telegram_notify(ad)
