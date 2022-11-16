from datetime import datetime
import json
import re
from time import sleep

from selenium import webdriver

from notifications_from_sahibinden.utils.mongo import get_db
from notifications_from_sahibinden.utils.telegram import send_ad_to_telegram


def save_data(data):
    file_name = datetime.now().strftime('%y%m%d%H%M') + '.json'
    with open(file_name, 'w') as file:
        json.dump(data, file)


def get_data(
        url: str = 'https://www.sahibinden.com/ajax/mapSearch/classified/markers?',
        date: str = 'date=1day',
        address_country: str = 'address_country=1',
        summary: str = 'm%3AincludeProjectSummaryFields=true',
        language: str = 'language=tr',
        category: str = 'category=16624',
        address_town: str = 'address_town=83',
        price_currency: str = 'price_currency=1',
        address_city: str = 'address_city=7',
        pagingOffset: str = 'pagingOffset=0',
        price_max: str = 'price_max=12000'
        ) -> json:

    link = url + '&'.join(
            [
                date,
                address_country,
                summary,
                language,
                category,
                address_town,
                price_currency,
                address_city,
                pagingOffset,
                price_max
            ]
        )

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    driver.get('https://www.sahibinden.com')
    sleep(4)
    print(link)
    driver.get(link)
    html = driver.page_source
    data = json.loads(re.sub(r'(\<([^>]+)>)', '', html))
    sleep(4)
    driver.close()
    driver.quit()
    return data['classifiedMarkers']


def processing_data():
    flats = get_db().flats
    now_time = datetime.now()
    for ad in get_data():
        ad['_id'] = ad.pop('id')
        if int(ad['_id']) < 1000000000 and not ad['thumbnailUrl']:
            continue
        exist = flats.find_one({'_id': ad['_id']})
        if not exist:
            ad['history_price'] = [(ad['price'], now_time)]
            ad["last_seen"] = now_time
            ad["last_update"] = now_time
            ad["removed"] = False
            flats.insert_one(ad)
        else:
            if exist['history_price'][-1][0] != ad['price']:
                exist["history_price"].append((ad['price'], now_time))
                exist["last_update"] = now_time
            exist["last_seen"] = now_time
            exist["removed"] = False
            flats.find_one_and_replace({"_id": ad['_id']}, exist)

    removed = flats.update_many({'last_seen': {'$lt': now_time}},
                                {'$set': {'removed': True}})
    updated = list(flats.find({'last_update': {'$gte': now_time}}))
    if updated:
        for i, ad in enumerate(updated):
            send_ad_to_telegram(ad)
            sleep(5)
