from telegram.ext import ApplicationBuilder, AIORateLimiter

from config import telegram_config
from bot.conversation import setup_conversation, setup_cancel
from bot.get_id import setup_get_id

limiter = AIORateLimiter(max_retries=10)
application = ApplicationBuilder().token(telegram_config.token_antalya_bot).rate_limiter(limiter).build()
setup_conversation(application)
setup_cancel(application)
setup_get_id(application)


def start_bot() -> None:
    application.run_polling()
