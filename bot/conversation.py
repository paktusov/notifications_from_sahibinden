from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler

PRICE, CHECK, CONFIRM = range(3)


def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Продолжить']]
    update.message.reply_text(
        "Привет, ищешь квартиру в Антилии? Пройди опрос, чтоб я смог присылать тебе подходящие варианты. В любой момент нажми /cancel, чтобы отменить",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PRICE


def price(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Сколько ты готов потратить TL на аренду? (в месяц)"
    )
    return CONFIRM


def check(update: Update, context: CallbackContext) -> range:
    try:
        context.user_data["price"] = update.message.text
    except ValueError:
        update.message.reply_text("Цена должна быть числом")
        return PRICE

    reply_keyboard = [['Да', 'Нет']]
    update.message.reply_text(
        f"Спасибо! Ты ищешь квартиру по этим параметрам:\n - Цена до {context.user_data['price']}",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CONFIRM


def confirm(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Отлично! Жди уведомлений о новых квартирах")
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("До свидания! Уведомления отключены")
    return ConversationHandler.END


def setup_conversation(dispatcher: Dispatcher) -> None:
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                PRICE: [CallbackQueryHandler(price)],
                CHECK: [CallbackQueryHandler(check)],
                CONFIRM: [
                    MessageHandler(Filters.regex('^Да'), confirm),
                    MessageHandler(Filters.regex('^Нет'), price),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )
