import logging

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Application,
    ContextTypes, filters
)

from bot.models import Subscriber, SubscriberParameters
from mongo import db

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


PRICE, CHECK, CONFIRM = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.chat.id
    context.user_data["user_id"] = user_id
    reply_keyboard = [[
        InlineKeyboardButton("Продолжить", callback_data="continue"),
        InlineKeyboardButton("Отмена", callback_data="cancel"),
    ]]

    await context.bot.send_message(
        user_id,
        "Привет, ищешь квартиру в Антилии? Пройди опрос, чтоб я смог присылать тебе подходящие варианты.",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return PRICE


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        context.user_data.get("user_id"),
        "Какую максимальную сумму TL ты готов потратить на аренду в месяц?"
    )
    return CHECK


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> range:
    try:
        context.user_data["max_price"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Цена должна быть числом. Попробуй еще раз")
        # logging.info(update)
        return CHECK

    reply_keyboard = [[
        InlineKeyboardButton('Да', callback_data='Yes'),
        InlineKeyboardButton('Нет', callback_data='No'),
    ]]
    await update.message.reply_text(
        f"Спасибо! Ты ищешь квартиру по этим параметрам:\n - Цена до {context.user_data['max_price']}",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data["user_id"]
    subscriber = Subscriber(
        _id=user_id,
        parameters=SubscriberParameters(
            max_price=context.user_data["max_price"],
        ),
    )
    db.subscribers.find_one_and_replace({"_id": user_id}, subscriber.dict(by_alias=True), upsert=True)
    await context.bot.send_message(user_id, "Отлично! Жди уведомлений о новых квартирах")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # logging.info(update)
    user_id = context.user_data["user_id"]
    db.subscribers.find_one_and_update({"_id": user_id}, {"$set": {"active": False}})
    await context.bot.send_message(user_id, "До свидания! Уведомления отключены")
    return ConversationHandler.END


def setup_conversation(application: Application) -> None:
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                PRICE: [
                    CallbackQueryHandler(price, pattern="continue"),
                    CallbackQueryHandler(cancel, pattern="cancel"),
                    MessageHandler(filters.TEXT, start),
                ],
                CHECK: [MessageHandler(filters.TEXT, check)],
                CONFIRM: [
                    CallbackQueryHandler(confirm, pattern="Yes"),
                    CallbackQueryHandler(price, pattern="No"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_chat=False,

        )
    )
