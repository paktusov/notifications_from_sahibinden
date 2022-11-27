from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

from bot import send_ad_to_telegram, edit_ad_in_telegram, send_comment_for_ad_to_telegram
from notifications_from_sahibinden.mongo import db


class Price(BaseModel):
    price: float
    updated: datetime


class Ad(BaseModel):
    id: str = Field(alise='_id')
    created: datetime = Field(factory=datetime.now)
    last_update: datetime = Field(factory=datetime.now)
    last_seen: datetime = Field(factory=datetime.now)
    thumbnail_url: str = Field(alias='thumbnailUrl')
    history_price: list[Price] = Field(factory=list)
    telegram_channel_message_id: str = ''
    telegram_chat_message_id: str = ''
    removed: bool = False

    def from_sah(self, data: dict[str, Any]):
        data['_id'] = data.pop('id')
        return data

    @property
    def last_price(self):
        return self.history_price[-1].price

    @property
    def last_price_update(self):
        return self.history_price[-1].updated

    @property
    def short_url(self):
        return f'https://www.sahibinden.com/{self.id}'

    def update_from_existed(self, existed: 'Ad'):
        if existed.last_price != self.last_price:
            self.history_price = existed.history_price + self.history_price

        self.telegram_channel_message_id = existed.telegram_channel_message_id
        self.telegram_chat_message_id = existed.telegram_chat_message_id
        self.created = existed.created

    def save(self):
        db.flats.insert_one(self.dict())
        self.telegram_notify()

    def telegram_notify(self):
        if self.removed:
            edit_ad_in_telegram(self, 'remove')
        elif len(self.history_price) == 1 and self.last_update == self.created:
            send_ad_to_telegram(self)
        elif self.last_price_update == self.last_update:
            send_comment_for_ad_to_telegram(self)
            edit_ad_in_telegram(self, 'update')

    def remove(self):
        self.removed = True
        self.save()
