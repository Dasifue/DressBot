import smtplib
import os
import datetime
from email.message import EmailMessage
from email.policy import default

from telebot import types
from sqlalchemy import exc
from dotenv import load_dotenv

from bot import BOT as bot
from database import DBManager, ENGINE


load_dotenv()


manager = DBManager(engine=ENGINE)


@bot.message_handler(commands=['start'])
def start(message: types.Message, edit_message=False):
    text = f"Hello, {message.chat.username}! I'm Dress Bot.\nWould you like to see my catalog?"

    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton(text="Open catalog!", callback_data="catalog"),
        types.InlineKeyboardButton(text="Info", url="https://www.python.org/")
    ]

    user_id = message.chat.id
    if manager.get_user(user_id=user_id) is not None:
        button = types.InlineKeyboardButton(text="Show cart", callback_data="show_cart")
        buttons.insert(1, button)
    
    markup.add(*buttons)

    if edit_message:
        bot.edit_message_text(
            text=text, 
            chat_id=message.chat.id, 
            message_id=message.id, 
            reply_markup=markup
        )
    else:
        bot.send_message(
            chat_id=message.chat.id, 
            text=text, 
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: call.data=="catalog")
def send_categories(call: types.CallbackQuery):
    text = "Choose category!"

    markup = types.InlineKeyboardMarkup(row_width=2)

    categories = manager.select_categories("id", "name").fetchall()
    for category in categories:
        button = types.InlineKeyboardButton(text=category[1], callback_data=f"category://{category[0]}") #category://1
        markup.add(button)
    
    back_button = types.InlineKeyboardButton(text="Back to main menu", callback_data="back://main")
    markup.add(back_button)

    bot.edit_message_text(
        text=text, 
        chat_id=call.message.chat.id, 
        message_id=call.message.id, 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("category://"))
def send_dress_by_category(call: types.CallbackQuery, dress = None):
    text = "Click on dress"


    markup = types.InlineKeyboardMarkup(row_width=2)

    if dress is None:
        category_id = call.data.replace("category://", "")
        dress = manager.select_category_dress(category_id, "id", "name").fetchall()
    

    for d in dress:
        button = types.InlineKeyboardButton(text=d[1], callback_data=f"dress://{d[0]}") #dress://5
        markup.add(button)

    back_button = types.InlineKeyboardButton(text="Back to categories", callback_data="back://categories")
    markup.add(back_button)

    bot.edit_message_text(
        text=text, 
        chat_id=call.message.chat.id, 
        message_id=call.message.id, 
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("dress://"))
def send_dress(call: types.CallbackQuery, dress = None):

    if dress is None:
        dress_id = call.data.replace("dress://", "")
        dress = manager.select_dress(dress_id=dress_id).fetchone()

    total_price = dress[4] - dress[4] * dress[5] / 100

    text = f"""
    {dress[2]}

    {dress[3]}

    Price: ${total_price} (${dress[4]} - {dress[5]}%)
    """
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton(text="Add to cart", callback_data=f"add_to_cart://{dress[0]}")
    markup.add(button)

    try:
        with open(file=dress[6], mode="rb") as file:
            file = file.read()
            bot.send_photo(chat_id=call.message.chat.id, photo=file, caption=text, reply_markup=markup)
    except Exception as ex:
        print(ex)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup
        )        


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_to_cart://"))
def add_to_cart(call: types.CallbackQuery):
    user_id = call.message.chat.id

    dress_id = call.data.replace("add_to_cart://", "")

    markup = types.InlineKeyboardMarkup(row_width=1)
    try:
        cart = manager.get_user_cart(user_id=user_id)
        manager.insert_cart_product(cart_id=cart[0], dress_id=dress_id)
        bot.send_message(chat_id=call.message.chat.id, text="Успешно добавдено в корзину!")

    except exc.IntegrityError:
        text = f"Вы не прошли регистрацию" 

        register_button = types.InlineKeyboardButton(text="Пройти регистрацию", callback_data="start_registration")

        markup.add(register_button)

        bot.send_message(
        text=text, 
        chat_id=call.message.chat.id, 
        reply_markup=markup,

    )
    else:
        pass


@bot.callback_query_handler(func=lambda call: call.data=="start_registration")
def start_registration(call: types.CallbackQuery):
    text = """
    Введите вашу почту и номер телефона.
    Пример:
    example@gmail.com
    +996(555)44-33-22

    Номер телефона и почта должны быть на разных линиях
    """
    message = bot.send_message(chat_id=call.message.chat.id, text=text)
    bot.register_next_step_handler(message=message, callback=register)




def register(message: types.Message):
    data = {}
    data['id'] = str(message.from_user.id)
    data['username'] = message.from_user.username
    data['first_name'] = message.from_user.first_name
    data['last_name'] = message.from_user.last_name

    try:
        message_data = message.text.split("\n")
        data['email'] = message_data[0].strip()
        data['phone_number'] = message_data[1].strip()

        data = {key: f'"{value}"' for key, value in data.items() if value is not None}

        manager.insert_user(data=data)
    except IndexError:
        bot.send_message(chat_id=message.chat.id, text="Данные были отпавлены в неправильном формате!")
    except exc.IntegrityError:
        bot.send_message(chat_id=message.chat.id, text="Вы уже зарегистрированны или данная почта уже использовалась!")
    else:
        bot.send_message(chat_id=message.chat.id, text="Вы успешно зарегистрировались!")




@bot.callback_query_handler(func=lambda call: call.data=="show_cart")
def show_cart_poducts_handler(call: types.CallbackQuery):
    user_id = call.message.chat.id
    cart = manager.get_user_cart(user_id=user_id)
    cart_products = manager.select_cart_products(cart_id=cart[0]).fetchall()

    markup = types.InlineKeyboardMarkup(row_width=3)

    cart_price = 0

    for product in cart_products:
        dress = manager.select_dress(product[1], "id", "name", "price", "discount").fetchone()
        total_price = round(dress[2] - dress[2] * dress[3] / 100, 2)
        cart_price += total_price
        button = types.InlineKeyboardButton(text=f"{dress[1]} - ${total_price}", callback_data=f"delete://{product[0]}")
        markup.add(button)
    
    checkout = types.InlineKeyboardButton(text="Checkout order", callback_data="checkout")
    back_button = types.InlineKeyboardButton(text="Back to main menu", callback_data="back://main")
    markup.add(checkout, back_button)
    
    text = f"Total price for cart is ${cart_price}"
    bot.edit_message_text(
        text=text, 
        chat_id=call.message.chat.id, 
        message_id=call.message.id, 
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete://"))
def delete_from_cart_handler(call: types.CallbackQuery):
    cart_product_id = call.data.replace("delete://", "")

    manager.delete_cart_product(cart_product_id=cart_product_id)
    
    show_cart_poducts_handler(call=call)


@bot.callback_query_handler(func=lambda call: call.data=="checkout")
def checkout_handler(call: types.CallbackQuery):
    user_id = call.message.chat.id
    user = manager.get_user(user_id, "email")
    cart = manager.get_user_cart(user_id=user_id)
    cart_products = manager.select_cart_products(cart_id=cart[0]).fetchall()
    cart_price = 0

    data = []
    for product in cart_products:
        dress = manager.select_dress(product[1], "id", "name", "price", "discount").fetchone()
        total_price = round(dress[2] - dress[2] * dress[3] / 100, 2)
        cart_price += total_price
        data.append({"dress": dress[1], "price": total_price})


    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    sender = os.getenv("SENDER")
    password = os.getenv("PASSWORD")

    text = f"""
    Уважаемый(ая) {user[0]},

    Благодарим вас за оформление заказа в нашем интернет-магазине! Ваш заказ успешно принят, и мы готовы начать его обработку.

    Информация о заказе:
    Номер заказа: {cart[0]}
    Дата оформления: {datetime.datetime.now()}
    Сумма заказа: {cart_price}

    Состав заказа:
    {data}

    Способ оплаты: [Выбранный вами способ оплаты]

    Способ доставки: [Выбранный вами способ доставки]

    Ожидаемая дата доставки: [Предполагаемая дата доставки]

    Если у вас есть какие-либо вопросы или изменения к заказу, пожалуйста, свяжитесь с нашей службой поддержки по телефону [Номер телефона] или по электронной почте [Адрес электронной почты поддержки].

    Спасибо, что выбрали наш магазин! Мы ценим ваш бизнес и делаем все возможное, чтобы ваш опыт покупок был приятным.

    С уважением,
    DressBot
    {sender}
    """

    msg = EmailMessage(policy=default)
    msg["Subject"] = f"Покупка одежды в DressBot"
    msg["From"] = sender
    msg["To"] = user[0]
    msg.set_content(text)

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg=msg)


    text = f"Чек был отправлен вам на почту:  {user[0]}"
    bot.send_message(chat_id=call.message.chat.id, text=text)
    manager.deactivate_cart(cart_id=cart[0])




@bot.callback_query_handler(func=lambda call: call.data.startswith("back://"))
def back_to(call: types.CallbackQuery):

    if call.data.endswith("main"):
        start(message=call.message, edit_message=True)
    elif call.data.endswith("categories"):
        send_categories(call=call)
    elif call.data.endswith("_dress"):
        category_id = call.data.replace("back://", "").replace("_dress", "")
        dress = manager.select_category_dress(category_id, "id", "name").fetchall()
        send_dress_by_category(call=call, dress=dress)

    elif call.data.endswith("_dress_details"):
        dress_id = call.data.replace("back://", "").replace("_dress_details", "")
        dress = manager.select_dress(dress_id=dress_id).fetchone()
        send_dress(call=call, dress=dress)



__all__ = (
    'start',
    'send_categories',
    'send_dress_by_category',
    'send_dress',
    'add_to_cart',
    'delete_from_cart_handler',
    'show_cart_poducts_handler',
    'start_registration',
    'register',
    'back_to',
    'manager',
)

