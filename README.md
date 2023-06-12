# Чат-бот по продажи пиццы

Учебный проект по продаже товаров интернет-магазина `elasticpath.com` через Телеграм.  
Товары, клиенты, корзина товаров реализованы на базе интернет-магазина, связь с чат-ботом через API.

Чат-бот может показать список доступных товаров, выводит информацию о товаре, 
позволяет наполнить корзину, корректировать корзину заказов и оформить заказ.  

Для каждого пользователя сохраняется его "статус" - на каком шаге он остановился и используется для
анализа работы клиента в чат-боте.


## Как установить

Python3 должен быть уже установлен. Затем используйте pip (или pip3, если есть конфликт с Python2) для установки зависимостей:

```bash
pip install -r requirements.txt
```


## Пример использования

## Для работы чат-бота понадобятся следующие переменные окружения:

- Для доступа к Интернет-магазину в личном кабинете нужно сгенерировать:
```bash
MOTLIN_CLIENT_ID='your client_id'
MOTLIN_CLIENT_SECRET='your client_service'  
```
- Токен для вашего бота, полученный у `@BotFather`
```bash
TG_TOKEN='YOUR_TELEGRAM_BOT_TOKEN'
```
- для работы с геолокацией понадобится Яндекс.Геокодер. Получить API_key нужно [тут](https://developer.tech.yandex.ru/services/)
```bash
YANDEX_GEOCODER_API_KEY='YANDEX_GEOCODER_API_KEY'
```
- для реализации оплаты через Telegram понадобится 
```bash
PAYMENT_PROVIDER_TOKEN='YOUR_TOKEN'
```

## Запуск модуля

```bash
python pizza_bot.py
```

### Загрузка данных
Предусмотрена возможность автоматического заполнения справочников из файлов формата `json`.  
Для примера смотри `menu.json`, `addresses.json`.

- Загрузка списка товаров:
```bash
python loaddata.py -m menu.json
```
- Загрузка адресов пиццерий (адреса можно дополнить ключом `telegram_id` для работы уведомлений):
```bash
python loaddata.py -a addresses.json
```
Для тестирования доставки уведомлений используйте свой номер `telegram_id` и параметр `-tg`
```bash
python loaddata.py -a addresses.json -tg 123456789
```
- 
- Удаление справочников из базы
```bash
python loaddata.py -d
```

# Цель проекта

Код написан в образовательных целях на онлайн-курс для веб-разработчиков [Devman](dvmn.org).
