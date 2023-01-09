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
CHECK_PRICE = 2
CHECK_FLOOR = 3
CHECK_ROOMS = 4
CHECK_HEATING = 5
AREAS, CHECK_AREAS = range(6, 8)
CHECK_FURNITURE = 8
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
        """Привет, ищешь квартиру в Антилии? Я могу отправлять тебе уведомления о новых квартирах по твоим параметрам поиска.""",
    )
    await context.bot.send_message(
        user_id,
        "Чтобы начать, нажми 'Продолжить'",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return START


async def new_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
            InlineKeyboardButton("Районы", callback_data="towns"),
            InlineKeyboardButton("Мебель", callback_data="furniture"),
        ],
        [
            InlineKeyboardButton("Подписаться", callback_data="subscribe"),
        ],
    ]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Выбери требуемые параметры поиска и нажми 'Подписаться'",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return NEW_SUBSCRIBE


async def get_price(update:Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["max_price"] = context.user_data.get("max_price", ['30000'])
    callback_data = update.callback_query.data
    prices = ['5000', '7500', '10000', '12500', '15000', '20000', '25000']
    if callback_data != 'price':
        context.user_data['max_price'] = [callback_data]

    data = context.user_data['max_price']

    reply_keyboard = []
    for price in prices:
        if not reply_keyboard or len(reply_keyboard[-1]) == 2:
            reply_keyboard.append([])
        reply_keyboard[-1].append(inline_keyboard_button(price, price, data))
    reply_keyboard[-1].append(inline_keyboard_button('Любая', '30000', data))
    reply_keyboard.append([InlineKeyboardButton("Назад", callback_data="_back")])
    text = "Какую максимальную сумму TL ты готов потратить на аренду в месяц?"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_PRICE


async def get_floor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
            InlineKeyboardButton("Назад", callback_data="_back"),
        ],
    ]
    await update.callback_query.answer()
    text = "Выбери этажи, которые тебе подходят"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_FLOOR


async def get_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
            InlineKeyboardButton("Назад", callback_data="_back"),
        ],
    ]
    await update.callback_query.answer()
    text = "Какое количество комнат тебе нужно?"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_ROOMS


async def get_heating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["heating"] = context.user_data.get("heating", ["all"])
    callback_data = update.callback_query.data
    if callback_data in ["gas", "electricity", "underfloor", "central", "ac"]:
        if "all" in context.user_data["heating"]:
            context.user_data["heating"].remove("all")
        if callback_data not in context.user_data["heating"]:
            context.user_data["heating"].append(callback_data)
        else:
            context.user_data["heating"].remove(callback_data)
    elif callback_data == "all":
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
            InlineKeyboardButton("Назад", callback_data="_back"),
        ],
    ]
    await update.callback_query.answer()
    text = "Выбери тип отопления"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_HEATING


async def get_towns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    towns = db.towns.find()
    context.user_data["areas"] = context.user_data.get("areas", {})

    reply_keyboard = [[]]
    for town in towns:
        reply_keyboard[-1].append(InlineKeyboardButton(town["name"], callback_data=town["_id"]))
        if not "all_" + town["_id"] in context.user_data["areas"]:
            context.user_data["areas"]["all_" + town["_id"]] = False
    reply_keyboard.append([InlineKeyboardButton("Назад", callback_data="_back")])
    logging.info(context.user_data["areas"])
    await update.callback_query.answer()
    text = "Выбери город"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return AREAS


async def get_areas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    town_id, area, *_ = update.callback_query.data.split('&') + ['', '']
    areas = {area["name"]: False for area in db.areas.find({"town_id": town_id}).sort("name", 1)}
    if not area:
        context.user_data["areas"]["all_" + town_id] = True
        context.user_data["areas"].update(areas)
    elif area == "all":
        context.user_data["areas"]["all_" + town_id] = not context.user_data["areas"]["all_" + town_id]
        context.user_data["areas"].update(areas)
    else:
        context.user_data["areas"][area] = not context.user_data["areas"][area]
        context.user_data["areas"]["all_" + town_id] = False

    reply_keyboard = []
    for area in areas.keys():
        if not reply_keyboard or len(reply_keyboard[-1]) == 3:
            reply_keyboard.append([])
        reply_keyboard[-1].append(
            InlineKeyboardButton(
                text=f"{'✔' if context.user_data['areas'][area] else '✖'} {area}",
                callback_data="&".join([town_id, area])
            )
        )
    reply_keyboard[-1].append(
        InlineKeyboardButton(
            text=f"{'✔' if context.user_data['areas']['all_' + town_id] else '✖'} Любой",
            callback_data="&".join([town_id, "all"])
        )
    )
    reply_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="towns")])
    await update.callback_query.answer()
    text = "Выбери район"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_AREAS


async def get_furniture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["furniture"] = context.user_data.get("furniture", ["furnished", "unfurnished"])
    callback_data = update.callback_query.data
    if callback_data in ["furnished", "unfurnished"]:
        if callback_data in context.user_data["furniture"]:
            context.user_data["furniture"].remove(callback_data)
        else:
            context.user_data["furniture"].append(callback_data)

    if not context.user_data["furniture"]:
        context.user_data["furniture"] = ["furnished", "unfurnished"]

    data = context.user_data["furniture"]

    reply_keyboard = [
        [
            inline_keyboard_button("С мебелью", "furnished", data),
            inline_keyboard_button("Без мебели", "unfurnished", data),
        ],
        [
            InlineKeyboardButton("Назад", callback_data="_back"),
        ],
    ]
    await update.callback_query.answer()
    text = "Нужна ли мебель?"
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CHECK_FURNITURE


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
    price_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_price, pattern="price")],
        states={
            CHECK_PRICE: [
                CallbackQueryHandler(get_price, pattern="^[0-9]{1,6}$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    floor_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_floor, pattern="floor")],
        states={
            CHECK_FLOOR: [
                CallbackQueryHandler(get_floor, pattern="^[^_].*"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    rooms_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_rooms, pattern="rooms")],
        states={
            CHECK_ROOMS: [
                CallbackQueryHandler(get_rooms, pattern="^[^_].*"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    heating_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_heating, pattern="heating")],
        states={
            CHECK_HEATING: [
                CallbackQueryHandler(get_heating, pattern="^[^_].*"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    areas_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_towns, pattern="towns")],
        states={
            AREAS: [
                CallbackQueryHandler(get_areas, pattern="^[0-9]{1,2}$"),
            ],
            CHECK_AREAS: [
                CallbackQueryHandler(get_towns, pattern="towns"),
                CallbackQueryHandler(get_areas, pattern=".*"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
        map_to_parent={
            END: NEW_SUBSCRIBE,
        },
    )

    furniture_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_furniture, pattern="furniture")],
        states={
            CHECK_FURNITURE: [
                CallbackQueryHandler(get_furniture, pattern="^[^_].*"),
            ],
        },
        fallbacks=[CallbackQueryHandler(end_second_level, pattern="_back")],
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
                    price_conversation,
                    floor_conversation,
                    rooms_conversation,
                    heating_conversation,
                    areas_conversation,
                    furniture_conversation,
                    CallbackQueryHandler(subscribe, pattern="subscribe"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_chat=False,
            allow_reentry=True,
        )
    )
