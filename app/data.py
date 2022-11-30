from datetime import datetime
import json
import logging
import re
from urllib.parse import urlencode
from time import sleep
from typing import Any

from selenium import webdriver

from app.mongo import get_db
from app.models import Ad


SAHIBINDEN_HOST = 'https://www.sahibinden.com/ajax/mapSearch/classified/markers?'
SAHIBINDEN_DEFAULT_PARAMS = {
    'date': '1day',
    'address_country': '1',
    # 'm%3AincludeProjectSummaryFields': 'true',
    'language': 'tr',
    'category': '16624',
    'address_town': '83',
    'price_currency': '1',
    'address_city': '7',
    'pagingOffset': '0',
    'price_max': '12000',
}


def save_data(data):
    file_name = datetime.now().strftime('%y%m%d%H%M') + '.json'
    with open(file_name, 'w') as file:
        json.dump(data, file)


def get_data_from_sah(**url_params: Any) -> list[Ad]:
    link = SAHIBINDEN_HOST + urlencode({**SAHIBINDEN_DEFAULT_PARAMS, **url_params}) + '&m%3AincludeProjectSummaryFields=true'

    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-javascript")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )

    driver.get('https://www.sahibinden.com')
    sleep(4)
    logging.info(link)
    print(link)
    driver.get(link)
    html = driver.page_source
    data = json.loads(re.sub(r'(\<([^>]+)>)', '', html))
    sleep(4)
    driver.close()
    driver.quit()
    return [
        Ad(**row)
        for row in data['classifiedMarkers']
        if not (int(row['id']) < 1000000000 and not row['thumbnailUrl'])
    ]


def processing_data():
    flats = get_db().flats
    now_time = datetime.now()

    parsed_ads = get_data_from_sah()

    ids = [ad.id for ad in parsed_ads]

    existed_ads = {
        ad['_id']: Ad(**ad)
        for ad in flats.find({'_id': {'$in': ids}})
    }

    for ad in parsed_ads:
        if ad.id in existed_ads:
            ad.update_from_existed(existed_ads[ad.id])
        ad.save()

    # missed_ad = [
    #     Ad(**ad)
    #     for ad in flats.find({
    #         "last_seen": {"$lt": now_time},
    #         "removed": False
    #     })
    # ]
    # for ad in missed_ad:
    #     ad.remove()
