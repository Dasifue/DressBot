from telebot import TeleBot

from dotenv import load_dotenv
from os import getenv

load_dotenv()


BOT = TeleBot(token=getenv("TOKEN"))

