import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.models import Subscriber, SubscriberParameters
from mongo import db


logger = logging.getLogger(__name__)

START, NEW_SUBSCRIBE = range(2)
CHECK_PRICE, CONFIRM_PRICE = range(2, 4)
CHECK_FLOOR = 4
CHECK_ROOMS = 5
CHECK_HEATING = 6
END = ConversationHandler.END


def inline_keyboard_button(text: str, callback_data: str, data: list) -> InlineKeyboardButton:
    def markup(d):
        return f"{'✔' if d in data else '✖'}️"

    return InlineKeyboardButton(f"{markup(callback_data)} {text}", callback_data=callback_data)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.sender_chat:
        await context.bot.send_message(
            update.message.sender_chat.id,
            "Для подписки на уведомления, пожалуйста, напишите мне в личные сообщения @flat_in_Antalya_test_bot",
        )
        return ConversationHandler.END
    user_id = update.message.chat.id
    context.user_data["user_id"] = user_id
    if db.subscribers.find_one({"_id": user_id, "active": True}):
        await context.bot.send_message(
            user_id,
            "Ты уже подписан на уведомления. Чтобы отписаться, напиши /cancel",
        )
        return ConversationHandler.END

    reply_keyboard = [
        [
            InlineKeyboardButton("Продолжить", callback_data="continue"),
        ]
    ]
    await context.bot.send_message(
        user_id,
        """Привет, ищешь квартиру в Антилии?
         Я могу отправлять тебе уведомления о новых квартирах по твоим параметрам поиска.""",
    )
    await context.bot.send_message(
        user_id,
        "Чтобы начать, нажми 'Продолжить'",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return START


async def new_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    reply_keyboard = [
        [
            InlineKeyboardButton("Цена", callback_data="price"),
            InlineKeyboardButton("Этаж", callback_data="floor"),
        ],
        [
            InlineKeyboardButton("Комнаты", callback_data="rooms"),
            InlineKeyboardButton("Отопление", callback_data="heating"),
        ],
        [
            InlineKeyboardButton("Подписаться", callback_data="subscribe"),
        ],
    ]
    if update.callback_query:
        await update.callback_query.answer()
    if update.callback_query and update.callback_query.data == "continue":
        await update.callback_query.edit_message_text(
            "Выбери требуемые параметры поиска и нажми 'Подписаться'",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    else:
        await context.bot.send_message(
            user_id,
            "Выбери требуемые параметры поиска и нажми 'Подписаться'",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    return NEW_SUBSCRIBE


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    if not context.user_data.get("max_price"):
        return await add_price(update, context)

    reply_keyboard = [
        [
            InlineKeyboardButton("Подтвердить", callback_data="сonfirm"),
            InlineKeyboardButton("Изменить", callback_data="Change"),
        ]
    ]
    await context.bot.send_message(
        user_id,
        f"Ты ищешь квартиру с ценой до {context.user_data['max_price']} TL в месяц",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CONFIRM_PRICE


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await context.bot.send_message(
        context.user_data.get("user_id"), "Какую максимальную сумму TL ты готов потратить на аренду в месяц?"
    )
    return CHECK_PRICE


async def check_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["max_price"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Цена должна быть числом. Попробуй еще раз")
        return CHECK_PRICE
    return await price(update, context)


async def floor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    context.user_data["floor"] = context.user_data.get("floor", ["all"])
    callback_data = update.callback_query.data
    if callback_data in ["without_basement", "without_first", "without_last"]:
        if "all" in context.user_data["floor"]:
            context.user_data["floor"].remove("all")
        if callback_data in context.user_data["floor"]:
            context.user_data["floor"].remove(callback_data)
        else:
            context.user_data["floor"].append(callback_data)
    elif update.callback_query.data == "all":
        context.user_data["floor"] = ["all"]

    data = context.user_data["floor"]

    reply_keyboard = [
        [
            inline_keyboard_button("Любой", "all", data),
            inline_keyboard_button("Кроме подвала/цоколя", "without_basement", data),
        ],
        [
            inline_keyboard_button("Кроме первого этажа", "without_first", data),
            inline_keyboard_button("Кроме последнего этажа", "without_last", data),
        ],
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        ],
    ]
    await update.callback_query.answer()
    text = "Выбери этажи, которые тебе подходят"
    if callback_data == "floor":
        await context.bot.send_message(
            user_id,
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    return CHECK_FLOOR


async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    context.user_data["rooms"] = context.user_data.get("rooms", ["all"])
    callback_data = update.callback_query.data
    if callback_data in ["studio", "one", "two", "three", "four"]:
        if "all" in context.user_data["rooms"]:
            context.user_data["rooms"].remove("all")
        if callback_data in context.user_data["rooms"]:
            context.user_data["rooms"].remove(callback_data)
        else:
            context.user_data["rooms"].append(callback_data)
    elif update.callback_query.data == "all":
        context.user_data["rooms"] = ["all"]

    data = context.user_data["rooms"]

    reply_keyboard = [
        [
            inline_keyboard_button("Cтудия", "studio", data),
            inline_keyboard_button("Одна", "one", data),
        ],
        [
            inline_keyboard_button("Две", "two", data),
            inline_keyboard_button("Три", "three", data),
        ],
        [
            inline_keyboard_button("Четыре", "four", data),
            inline_keyboard_button("Любое количество", "all", data),
        ],
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        ],
    ]
    await update.callback_query.answer()
    text = "Какое количество комнат тебе нужно?"
    if callback_data == "rooms":
        await context.bot.send_message(
            user_id,
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    return CHECK_ROOMS


async def heating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    context.user_data["heating"] = context.user_data.get("heating", ["all"])
    callback_data = update.callback_query.data
    if callback_data in ["gas", "electricity", "underfloor", "central", "ac"]:
        if "all" in context.user_data["heating"]:
            context.user_data["heating"].remove("all")
        if callback_data not in context.user_data["heating"]:
            context.user_data["heating"].append(callback_data)
        else:
            context.user_data["heating"].remove(callback_data)
    elif update.callback_query.data == "all":
        context.user_data["heating"] = ["all"]

    data = context.user_data["heating"]

    reply_keyboard = [
        [
            inline_keyboard_button("Газовое", "gas", data),
            inline_keyboard_button("Электрическое", "electricity", data),
        ],
        [
            inline_keyboard_button("Теплый пол", "underfloor", data),
            inline_keyboard_button("Центральное", "central", data),
        ],
        [
            inline_keyboard_button("Кондиционер", "ac", data),
            inline_keyboard_button("Любое", "all", data),
        ],
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        ],
    ]
    await update.callback_query.answer()
    text = "Выбери тип отопления"
    if callback_data == "heating":
        await context.bot.send_message(
            user_id,
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
    return CHECK_HEATING


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await new_subscribe(update, context)
    return END


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    parameters = SubscriberParameters(**context.user_data)
    subscriber = Subscriber(
        _id=user_id,
        parameters=parameters,
        active=True,
    )
    db.subscribers.find_one_and_replace({"_id": user_id}, subscriber.dict(by_alias=True), upsert=True)
    await update.callback_query.answer()
    await context.bot.send_message(user_id, "Отлично! Жди уведомлений о новых квартирах")
    return END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data.get("user_id", update.message.from_user.id)
    db.subscribers.find_one_and_update({"_id": user_id}, {"$set": {"active": False}})
    await context.bot.send_message(user_id, "До свидания! Уведомления отключены")
    return END


def setup_cancel(application: Application) -> None:
    application.add_handler(CommandHandler("cancel", cancel))


def setup_conversation(application: Application) -> None:
    get_price = ConversationHandler(
        entry_points=[CallbackQueryHandler(price, pattern="price")],
        states={
            CONFIRM_PRICE: [
                CallbackQueryHandler(add_price, pattern="Change"),
                MessageHandler(filters.TEXT, price),
            ],
            CHECK_PRICE: [MessageHandler(filters.TEXT, check_price)],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="сonfirm")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    get_floor = ConversationHandler(
        entry_points=[CallbackQueryHandler(floor, pattern="floor")],
        states={
            CHECK_FLOOR: [
                CallbackQueryHandler(floor, pattern="without_basement"),
                CallbackQueryHandler(floor, pattern="without_first"),
                CallbackQueryHandler(floor, pattern="without_last"),
                CallbackQueryHandler(floor, pattern="all"),
                MessageHandler(filters.TEXT, floor),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="confirm")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    get_rooms = ConversationHandler(
        entry_points=[CallbackQueryHandler(rooms, pattern="rooms")],
        states={
            CHECK_ROOMS: [
                CallbackQueryHandler(rooms, pattern="one"),
                CallbackQueryHandler(rooms, pattern="two"),
                CallbackQueryHandler(rooms, pattern="three"),
                CallbackQueryHandler(rooms, pattern="four"),
                CallbackQueryHandler(rooms, pattern="studio"),
                CallbackQueryHandler(rooms, pattern="all"),
                MessageHandler(filters.TEXT, rooms),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="confirm")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    get_heating = ConversationHandler(
        entry_points=[CallbackQueryHandler(heating, pattern="heating")],
        states={
            CHECK_HEATING: [
                CallbackQueryHandler(heating, pattern="gas"),
                CallbackQueryHandler(heating, pattern="electricity"),
                CallbackQueryHandler(heating, pattern="underfloor"),
                CallbackQueryHandler(heating, pattern="central"),
                CallbackQueryHandler(heating, pattern="ac"),
                CallbackQueryHandler(heating, pattern="all"),
                MessageHandler(filters.TEXT, heating),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="confirm")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                START: [
                    CallbackQueryHandler(new_subscribe, pattern="continue"),
                    MessageHandler(filters.TEXT, start),
                ],
                NEW_SUBSCRIBE: [
                    get_price,
                    get_floor,
                    get_rooms,
                    get_heating,
                    CallbackQueryHandler(subscribe, pattern="subscribe"),
                    MessageHandler(filters.TEXT, new_subscribe),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_chat=False,
            # allow_reentry=True,
        )
    )
