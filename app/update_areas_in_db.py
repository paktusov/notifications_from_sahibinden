import logging

from mongo import db

from app.get_data import get_areas
from app.models import Area


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

CLOSED_AREAS: list[str] = [
    "Hurma Mah.",
    "Sarısu Mh.",
    "Liman Mah.",
    "Topçular Mh.",
]


def processing_areas() -> None:
    towns = db.towns.find()
    for town in towns:
        logger.info("Processing areas for %s", town["_id"])
        data = get_areas(town["_id"])
        if not data:
            logger.error("Can't parse areas from %s", town["_id"])
            continue
        for d in data:
            area = Area(town_id=town["_id"], **d)
            if db.areas.find_one({"_id": area.id}):
                continue
            if area.name in CLOSED_AREAS:
                area.is_closed = True
            db.areas.insert_one(area.dict(by_alias=True))


if __name__ == "__main__":
    processing_areas()
