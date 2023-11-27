from bot import BOT as bot

from handlers import *


if __name__ == "__main__":
    manager.create_tables()
    bot.infinity_polling()
