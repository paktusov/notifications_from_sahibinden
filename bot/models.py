from typing import Optional

from pydantic import BaseModel


class TelegramIdAd(BaseModel):
    _id: str
    telegram_channel_message_id: str
    telegram_chat_message_id: str


class SubscriberParameters(BaseModel):
    max_price: Optional[list[str]]
    floor: Optional[list[str]]
    rooms: Optional[list[str]]
    heating: Optional[list[str]]
    areas: Optional[dict[str, bool]]
    furniture: Optional[list[str]]


class Subscriber(BaseModel):
    _id: str
    active: bool = False
    parameters: SubscriberParameters
