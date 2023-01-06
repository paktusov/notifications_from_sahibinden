import logging

from mongo import db

from app.get_data import get_areas
from app.models import Area


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def processing_areas() -> None:
    cities = db.cities.find()
    for city in cities:
        logger.info("Processing areas for %s", city["_id"])
        data = get_areas(city["_id"])
        if not data:
            logger.error("Can't parse areas from %s", city["_id"])
            continue
        for d in data:
            area = Area(city_id=city["_id"], **d)
            if db.areas.find_one({"_id": area.id}):
                continue
            db.areas.insert_one(area.dict(by_alias=True))


if __name__ == "__main__":
    processing_areas()
