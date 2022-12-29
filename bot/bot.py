from telegram.ext import ApplicationBuilder, BaseRateLimiter, AIORateLimiter

from config import telegram_config
from bot.conversation import setup_conversation
from bot.get_id import setup_get_id

application = ApplicationBuilder().token(telegram_config.token_antalya_bot).rate_limiter(AIORateLimiter(max_retries=10)).build()
setup_conversation(application)
setup_get_id(application)


def start_bot() -> None:
    application.run_polling()
