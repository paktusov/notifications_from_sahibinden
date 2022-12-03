import pymongo
from config import mongo_config


def get_db():
    client = pymongo.MongoClient(mongo_config.uri, mongo_config.port)
    return client[mongo_config.database]


db = get_db()
