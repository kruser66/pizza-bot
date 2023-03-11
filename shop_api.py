import requests
from slugify import slugify
from environs import Env


API_BASE_URL = 'https://api.moltin.com/v2'


def client_credentials_access_token(client_id, client_secret):
    url_api = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post(url_api, data=data)
    response.raise_for_status()

    return response.json()


def fetch_products(access_token):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    products = requests.get(url, headers=headers)
    products.raise_for_status()

    return products.json()['data']


def get_product_by_id(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    products = requests.get(url, headers=headers)
    products.raise_for_status()

    return products.json()['data']


def take_product_image_description(access_token, product) -> dict:

    file_id = product['relationships']['main_image']['data']['id']
    url_api = f'https://api.moltin.com/v2/files/{file_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(url_api, headers=headers)
    response.raise_for_status()

    response_image = response.json()['data']

    image_description = {
        'url': response_image['link']['href'],
        'filename': response_image['file_name']
    }

    return image_description


def get_cart(access_token, cart_id):
    url_api = f'https://api.moltin.com/v2/carts/{cart_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url_api, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def delete_cart(access_token, cart_id):
    url_api = f'https://api.moltin.com/v2/carts/{cart_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.delete(url_api, headers=headers)
    response.raise_for_status()

    return response


def add_product_to_cart(access_token, card_id, product_id, amount=1):

    items = get_cart_items(access_token, card_id)
    item = [item for item in items if item['product_id'] == product_id]

    if item:
        response = update_item_to_cart(access_token, card_id, product_id, item[0], amount)
    else:
        response = add_item_to_cart(access_token, card_id, product_id, amount)

    return response


def add_item_to_cart(access_token, card_id, product_id, amount):
    url = f'https://api.moltin.com/v2/carts/{card_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': amount,
        }
    }
    response = requests.post(url, headers=headers, json=params)
    return response.json()


def update_item_to_cart(access_token, card_id, product_id, item, amount):

    url = f'https://api.moltin.com/v2/carts/{card_id}/items/{item["id"]}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': item['quantity'] + amount,
        }
    }
    response = requests.put(url, headers=headers, json=params)
    return response.json()


def delete_item_from_cart(access_token, card_id, item_id):

    url = f'https://api.moltin.com/v2/carts/{card_id}/items/{item_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.delete(url, headers=headers)
    return response.json()


def get_cart_items(access_token, card_id):

    url = f'https://api.moltin.com/v2/carts/{card_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_customers(access_token):
    url_api = 'https://api.moltin.com/v2/customers'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url_api, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def update_or_create_customer(access_token, customer):
    filtered_customer = fetch_customer_by_email(access_token, customer['email'])
    if filtered_customer:
        update_customer(access_token, filtered_customer[0]['id'], customer)
    else:
        add_customer(access_token, customer)


def fetch_customer_by_email(access_token, user_email):
    url_api = 'https://api.moltin.com/v2/customers'

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    params = {
        'filter': f'eq(email,{user_email})'
    }

    response = requests.get(url_api, headers=headers, params=params)
    response.raise_for_status()

    return response.json()['data']


def add_customer(access_token, customer):
    url = f'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'customer',
        }
    }
    params['data'].update(customer)

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()


def update_customer(access_token, customer_id, customer):
    url = f'https://api.moltin.com/v2/customers/{customer_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'customer',
        }
    }
    params['data'].update(customer)

    response = requests.put(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()


def create_product(access_token, product):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'product',
            'name': product['name'],
            'slug': slugify(product['name']),
            'sku': str(product['id']),
            'description': product['description'],
            'manage_stock': False,
            'price': [
                {
                    'amount': product['price'],
                    'currency': 'RUB',
                    'includes_tax': True
                }
            ],
            'status': 'live',
            'commodity_type': 'physical'
        }
    }

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    product_id = response.json()['data']['id']
    file_id = create_file(access_token, product['product_image']['url'])
    main_image_relationship(access_token, product_id, file_id)


def create_file(access_token, image_url):
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    files = {
        'file_location': (None, image_url)
    }

    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()

    return response.json()['data']['id']


def main_image_relationship(access_token, product_id, file_id):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'main_image',
            'id': file_id,
        }
    }

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()


def delete_product(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    print(f'Deleted: {product_id}')


def delete_files(access_token):
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    files = response.json()['data']
    for file in files:
        url = f'https://api.moltin.com/v2/files/{file["id"]}'
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        response = requests.delete(url, headers=headers)
        response.raise_for_status()

        print(f'Deleted: {file["id"]}')


def create_flow(access_token, flow, fields):
    url = 'https://api.moltin.com/v2/flows'
    flow_name, flow_slug, flow_description = flow
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'flow',
            'name': flow_name,
            'slug': flow_slug,
            'description': flow_description,
            'enabled': True,
        }
    }

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    flow = response.json()['data']
    flow_id = flow['id']

    for field_name, field_type in fields.items():
        create_fields(access_token, flow_id, field_name, field_type)

    return flow


def fetch_flows(access_token):
    url = 'https://api.moltin.com/v2/flows'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def delete_flow(access_token, flow_id):
    url = f'https://api.moltin.com/v2/flows/{flow_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def create_fields(access_token, flow_id, field_name, filed_type):
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'field',
            'name': field_name,
            'slug': field_name,
            'field_type': filed_type,
            'description': f'Field for {field_name}',
            'required': False,
            'enabled': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id
                    }
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()['data']


def create_entries(access_token, flow_slug, entry):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    params = {
        'data': {
            'type': 'entry',
        }
    }
    params['data'].update(entry)

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()['data']


def fetch_entries(access_token, flow_slug):
    url_api = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url_api, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_entry(access_token, flow_slug, entry_id):
    url_api = f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(url_api, headers=headers)
    response.raise_for_status()

    return response.json()['data']


if __name__ == '__main__':

    env = Env()
    env.read_env()

    client_id = env.str('MOTLIN_CLIENT_ID')
    client_secret = env.str('MOTLIN_CLIENT_SECRET')

    token = client_credentials_access_token(client_id, client_secret)

    access_token = token['access_token']
