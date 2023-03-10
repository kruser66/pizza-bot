import json
import argparse
from environs import Env
from requests.exceptions import HTTPError
from shop_api import (
    client_credentials_access_token,
    create_product,
    fetch_products,
    delete_product,
    delete_files,
    create_flow,
    create_entries
)


def create_parser():
    parser = argparse.ArgumentParser(
        description='''
        Загрузка справочника продуктов и адресов ресторанов в интернет-магазин Motlin.
        Определите переменные окружения: MOTLIN_STORE_ID, MOTLIN_CLIENT_ID, MOTLIN_CLIENT_SECRET
        '''
    )
    parser.add_argument('-m', '--menu', nargs='?', help='json-файл со справочником меню')
    parser.add_argument('-a', '--addr', nargs='?', help='json-файл со справочником адресов ресторана')
    parser.add_argument('-tg', '--tg_id', nargs='?', help='Тестовый телеграм ID для отправки уведомлений по доставке')
    parser.add_argument('-d', action='store_true', help='удалить справочники из базы')

    return parser


def upload_menu(access_token):
    with open('example/menu.json', 'rb') as f:
        menu = json.load(f)

    for item in menu:
        create_product(access_token, item)
        print(f'Created: {item["name"]}')


def create_pizzerias_flow(access_token):
    flow = ('Pizzerias', 'pizzerias', 'Flow for pizzerias data')
    fields = {
        'address': 'string',
        'alias': 'string',
        'longitude': 'float',
        'latitude': 'float',
        'telegram_id': 'integer'
    }
    flow = create_flow(access_token, flow, fields)
    return flow


def upload_addresses(access_token, telegram_id=None):
    try:
        flow = create_pizzerias_flow(access_token)
    except HTTPError:
        print('Flow "address" уже загружен. Удалите данные перед повторной загрузкой')
        return

    with open('example/addresses.json', 'rb') as f:
        addresses = json.load(f)

    for address in addresses:
        entry = {
            'address': address['address']['full'],
            'alias': address['alias'],
            'longitude': float(address['coordinates']['lon']),
            'latitude': float(address['coordinates']['lat']),
            }
        if address.get('telegram_id'):
            entry.update({'telegram_id': address['telegram_id']})
        elif telegram_id:
            entry.update({'telegram_id': int(telegram_id)})

        create_entries(access_token, flow['slug'], entry)
        print(f'Upload: {entry["alias"]} {entry["address"]}')


if __name__ == '__main__':

    env = Env()
    env.read_env()
    client_id = env.str('MOTLIN_CLIENT_ID')
    client_secret = env.str('MOTLIN_CLIENT_SECRET')
    access_token = client_credentials_access_token(client_id, client_secret)['access_token']

    parser = create_parser()
    args = parser.parse_args()

    if args.menu:
        print('Try load menu')
        upload_menu(access_token)
    elif args.addr:
        print('Try load address')
        if args.tg_id:
            upload_addresses(access_token, args.tg_id)
        else:
            upload_addresses(access_token)
    elif args.d:
        print('Delete data')
        products = fetch_products(access_token)
        for product in products:
            delete_product(access_token, product['id'])
        delete_files(access_token)
    else:
        parser.print_help()

