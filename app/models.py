from datetime import datetime
from pydantic import BaseModel, Field, root_validator
from typing import Any, Optional
import logging

from bot import send_ad_to_telegram, edit_ad_in_telegram, send_comment_for_ad_to_telegram
from app.mongo import db


class Price(BaseModel):
    price: float
    updated: datetime


class Ad(BaseModel):
    id: str = Field(alias='_id')
    created: datetime
    last_update: datetime
    last_seen: datetime
    thumbnail_url: str = Field(alias='thumbnailUrl', default='')
    history_price: list[Price] = Field(default_factory=list)
    telegram_channel_message_id: Optional[str]
    telegram_chat_message_id: Optional[str]
    removed: bool = False
    last_condition_removed = False
    title: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    attributes: Optional[dict[str, str]]
    url: Optional[str]


    @property
    def last_price(self):
        return self.history_price[-1].price

    @property
    def first_price(self):
        return self.history_price[0].price

    @property
    def last_price_update(self):
        return self.history_price[-1].updated

    @property
    def short_url(self):
        return f'https://www.sahibinden.com/{self.id}'

    @root_validator(pre=True)
    def init_ad(cls, values):
        now = datetime.now()
        values['last_update'] = values.get('last_update', now)
        values['last_seen'] = now
        values['created'] = values.get('created', now)
        if not values.get('history_price'):
            values['history_price'] = [Price(price=values['price'], updated=now)]
        # values['history_price'] = values.get('history_price', [Price(price=values['price'], updated=now)])
        if values.get('id'):
            values['_id'] = values.pop('id')
        return dict(
            **values
        )

    def update_from_existed(self, existed: 'Ad'):
        self.telegram_channel_message_id = existed.telegram_channel_message_id
        self.telegram_chat_message_id = existed.telegram_chat_message_id
        self.created = existed.created

        if existed.last_price != self.last_price:
            self.history_price = existed.history_price + self.history_price
            self.last_update = self.last_price_update
        else:
            self.history_price = existed.history_price
            self.last_update = existed.last_update

        if existed.removed:
            self.last_condition_removed = True

    def save(self):
        db.flats.find_one_and_replace({"_id": self.id}, self.dict(by_alias=True), upsert=True)
        logging.debug(f'Ad {self.id} added or updated in db')
        self.telegram_notify()
        logging.debug(f'Ad {self.id} notified to telegram')

    def telegram_notify(self):
        if self.removed:
            edit_ad_in_telegram(self, 'remove')
        elif self.last_seen == self.created:
            send_ad_to_telegram(self)
        elif self.last_seen == self.last_update:
            send_comment_for_ad_to_telegram(self)
            edit_ad_in_telegram(self, 'update')
        elif self.last_condition_removed:
            if len(self.history_price) == 1:
                edit_ad_in_telegram(self, 'new')
            else:
                edit_ad_in_telegram(self, 'update')

    def remove(self):
        self.last_condition_removed = False
        self.removed = True
