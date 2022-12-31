from typing import Optional

from pydantic import BaseModel


class TelegramIdAd(BaseModel):
    _id: str
    telegram_channel_message_id: str
    telegram_chat_message_id: str


class SubscriberParameters(BaseModel):
    max_price: Optional[int]


class Subscriber(BaseModel):
    _id: str
    active: bool = True
    parameters: SubscriberParameters