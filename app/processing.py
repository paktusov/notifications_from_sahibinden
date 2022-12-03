from datetime import datetime
import logging

from app.get_data import create_models_from_data, get_data_with_selenium, get_data_with_cookies
from app.mongo import get_db
from app.models import Ad


def processing_data():
    flats = get_db().flats
    now_time = datetime.now()

    parsed_ads = create_models_from_data(get_data_with_cookies())

    ids = [ad.id for ad in parsed_ads]

    existed_ads = {
        ad['_id']: Ad(**ad)
        for ad in flats.find({'_id': {'$in': ids}})
    }

    for ad in parsed_ads:
        if ad.id in existed_ads:
            ad.update_from_existed(existed_ads[ad.id])
        ad.save()
        logging.info(f'Ad {ad.id} saved')

    missed_ad = [
        Ad(**ad)
        for ad in flats.find({
            "last_seen": {"$lt": now_time},
            "removed": False
        })
    ]
    for ad in missed_ad:
        ad.remove()
        ad.save()
