import os
import shelve
import logging
import requests
from textwrap import dedent
from datetime import datetime
from environs import Env
from functools import wraps
from email_validate import validate
from urllib.parse import unquote, urlsplit, urlparse
from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)

from telegram.constants import CHATACTION_TYPING, CHATACTION_UPLOAD_PHOTO
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from shop_api import (
    fetch_products, get_product_by_id, client_credentials_access_token, take_product_image_description,
    add_product_to_cart, delete_item_from_cart, get_cart_items, get_cart, add_customer
)
from pprint import pprint


logger = logging.getLogger(__name__)

IMAGES = 'images'


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    try:
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    except (KeyError, AttributeError):
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

    return lon, lat


def download_image(image_url, image_name):
    response = requests.get(image_url)
    if response.ok:
        with open(image_name, 'wb') as file:
            file.write(response.content)

    return response.ok


def build_main_menu(access_token, chat_id, products):
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])
    items = get_cart_items(access_token, chat_id)
    if items:
        keyboard.append([InlineKeyboardButton(f'Корзина ({len(items)})', callback_data='Корзина')])

    return keyboard


def build_product_menu(access_token, chat_id, product_id):
    keyboard = [[]]
    keyboard.append([InlineKeyboardButton('Добавить в корзину', callback_data=product_id)])
    items = get_cart_items(access_token, chat_id)
    if items:
        keyboard.append([InlineKeyboardButton(f'Корзина ({len(items)})', callback_data='Корзина')])
    keyboard.append([InlineKeyboardButton('Назад', callback_data='Назад')])

    return keyboard


def start(update, context):
    access_token = update_token(context)

    chat_id = update.message.chat_id

    products = fetch_products(access_token)
    keyboard = build_main_menu(access_token, chat_id, products)
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text='Выберите продукт:', reply_markup=reply_markup)

    return 'HANDLE_MENU'


def product_detail(update, context):
    access_token = update_token(context)
    query = update.callback_query
    chat_id = query.message.chat_id
    product_id = query.data
    context.user_data['product_id'] = product_id

    product = get_product_by_id(access_token, product_id)
    image = take_product_image_description(access_token, product)

    image_url = image['url']
    image_filename = os.path.basename(unquote(urlparse(image_url).path))
    path = os.path.join(IMAGES, image_filename)
    if not os.path.exists(path):
        download_image(image_url, path)

    keyboard = build_product_menu(access_token, chat_id, product_id)
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = dedent(
        f'''
        {product['name']}

        Price: {product['price'][0]['amount']} {product['price'][0]['currency']}

        {product['description'][:200]}...

        Заказать:
        '''
    )

    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(path, 'rb'),
        caption=text,
        reply_markup=reply_markup,
    )

    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    return 'HANDLE_DESCRIPTION'


def product_order(update, context):
    access_token = update_token(context)
    product_id = context.user_data['product_id']
    query = update.callback_query

    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if query.data == 'Назад':

        products = fetch_products(access_token)
        keyboard = build_main_menu(access_token, chat_id, products)
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(
            chat_id=chat_id,
            text='Выберите продукт:',
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )

        return 'HANDLE_MENU'

    else:
        product_id = query.data
        amount = 1
        add_product_to_cart(access_token, chat_id, product_id, amount)
        query.answer('Товар добавлен в корзину.')
        keyboard = build_product_menu(access_token, chat_id, product_id)
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_reply_markup(
            reply_markup=reply_markup)

        return 'HANDLE_DESCRIPTION'


def show_cart(update, context):
    access_token = update_token(context)
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

    if query.data == 'В меню':

        products = fetch_products(access_token)
        keyboard = build_main_menu(access_token, chat_id, products)
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text='Выберите продукт:',
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )

        return 'HANDLE_MENU'

    elif query.data == 'Корзина':
        pass
    else:
        item_id = query.data
        delete_item_from_cart(access_token, chat_id, item_id)

    items = get_cart_items(access_token, chat_id)
    cart = get_cart(access_token, chat_id)

    text = 'Ваша корзина: \n\n'
    for item in items:
        price = item['meta']['display_price']['with_tax']['unit']['formatted']
        summa = item['meta']['display_price']['with_tax']['value']['formatted']
        text += f'{item["name"]}\n{item["quantity"]} шт. по цене: {price} на сумму: {summa}\n\n'

    total = cart['meta']['display_price']['with_tax']['formatted']
    text += f'Общая сумму заказа: {total}'

    keyboard = []
    if items:
        keyboard.append([InlineKeyboardButton('Оплатить', callback_data='Оплатить')])
    for item in items:
        keyboard.append(
            [InlineKeyboardButton(f'Убрать из корзины {item["name"]}', callback_data=item['id'])]
        )
    keyboard.append([InlineKeyboardButton('В меню', callback_data='В меню')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )

    return 'HANDLE_CART'


def start_payment(update, context):
    if update.message:
        chat_id = update.message.chat_id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat_id

    keyboard = [[KeyboardButton('Отправить местоположение', request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    context.bot.send_message(
        chat_id=chat_id,
        text='Введите адрес доставки или отправьте местоположение.',
        reply_markup=reply_markup
    )

    return 'HANDLE_ADDRESS'


def fetch_address(update, context):
    api_key = context.bot_data['yandex_api_key']

    if not update.message.text:
        location = update.message.location
        address = (location['longitude'], location['latitude'])
    else:
        address_text = update.message.text
        address = fetch_coordinates(api_key, address_text)

    update.message.reply_text(
        text=f'Вы ввели адрес: {address}',
        # reply_markup=ReplyKeyboardRemove
    )

    # if update.message:
    #     chat_id = update.message.chat_id
    # elif update.callback_query:
    #     chat_id = update.callback_query.message.chat_id
    #
    # keyboard = [[KeyboardButton('Отправить номер телефона', request_contact=True)]]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    #
    # context.bot.send_message(
    #     chat_id=chat_id,
    #     text='Введите адрес доставки или отправьте местоположение.',
    #     reply_markup=reply_markup
    # )
    #
    # return 'HANDLE_EMAIL'


def echo_email(update, context):
    email = update.message.text
    access_token = update_token(context)

    if validate(email_address=email, check_format=True, check_blacklist=False, check_dns=False):
        update.message.reply_text(text=f'Вы ввели адрес: {email}')
        user = {
            'name': str(update.message.chat_id),
            'email': email
        }
        add_customer(access_token, user)
        return 'PAYMENT'
    else:
        update.message.reply_text(text=f'Адрес: {email} некорректный. Повторите ввод!')
        return 'HANDLE_EMAIL'


def handle_users_reply(update, context):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'Корзина':
        user_state = 'HANDLE_CART'
    elif user_reply == 'Оплатить':
        user_state = 'START_PAYMENT'
    else:
        with shelve.open('state') as db:
            user_state = db[str(chat_id)]

    states_functions = {
        'START': start,
        'HANDLE_MENU': product_detail,
        'HANDLE_DESCRIPTION': product_order,
        'HANDLE_CART': show_cart,
        'START_PAYMENT': start_payment,
        'HANDLE_ADDRESS': fetch_address,
        'HANDLE_EMAIL': echo_email
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        with shelve.open('state') as db:
            db[str(chat_id)] = next_state
    except Exception as err:
        print(err)
        logger.error(err)


def update_token(context):
    token = context.bot_data['token']
    now = datetime.timestamp(datetime.now())

    if now > token['expires']:
        token = client_credentials_access_token(context.bot_data['client_id'], context.bot_data['client_secret'])
        context.bot_data['token'] = token

    return token['access_token']


if __name__ == '__main__':
    os.makedirs(IMAGES, exist_ok=True)
    env = Env()
    env.read_env()

    logger.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.info('Запущен pizza-bot')

    # Получение токена для работы с интернет-магазином
    client_id = env.str('MOTLIN_CLIENT_ID')
    client_secret = env.str('MOTLIN_CLIENT_SECRET')
    motlin_token = client_credentials_access_token(client_id, client_secret)

    yandex_api_key = env.str('YANDEX_GEOCODER_API_KEY')

    token = env.str('TG_TOKEN')
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.bot_data = {
        'token': motlin_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'yandex_api_key': yandex_api_key
    }

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    updater.start_polling()
    updater.idle()
