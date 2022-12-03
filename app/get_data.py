from datetime import datetime
import json
import re
from urllib.parse import urlencode
from time import sleep
from typing import Any
import requests

from selenium import webdriver

from app.models import Ad


SAHIBINDEN_HOST = 'https://www.sahibinden.com/ajax/mapSearch/classified/markers'
SAHIBINDEN_DEFAULT_PARAMS = {
    'date': '7days', #1day
    'address_country': '1',
    'm:includeProjectSummaryFields': 'true',
    'language': 'tr',
    'category': '16624',
    'address_town': '83',
    'price_currency': '1',
    'address_city': '7',
    'pagingOffset': '0',
    'price_max': '12000',
}
COOKIES = {
    'vid': '831',
    'cdid': 'c50vCHNBN4SzpfX76373e4b9',
    '__ssid': '67ba7120581250b01a5b8d35baab3aa',
    '_gcl_au': '1.1.2131970503.1668539580',
    'OptanonAlertBoxClosed': '2022-11-15T19:14:44.197Z',
    'nwsh': 'std',
    'showPremiumBanner': 'false',
    'segIds': '',
    '_gid': 'GA1.2.1702292353.1668789633',
    'h28s1ZLRQ2': 'A9qeoIuEAQAAe_MKN-xHelX9Gcla-syrJUHTFiBKrXp9QQk65Kn-TPNiF-w_AVjoqhuucmW8wH8AADQwAAAAAA|1|0|bb001baedb500404d6d7059146f9dabfa9bd1f93',
    'MS1': 'https://www.sahibinden.com/ilan/emlak-konut-kiralik-tomas-gayrimenkul-2-plus1-esyali-kiralik-1058997090/detay',
    'userLastSearchSplashClosed': 'true',
    '_openContent': 'price%2Ca24%2Ca20%2Cdate',
    'dp': '1920*1080-landscape',
    'geoipCity': 'ankara',
    'geoipIsp': 'turk_telekom',
    '__cf_bm': 'uJ0q258JdYnSmg52gDglHhgR8yHDY7.wwN2tTlfM9wI-1670065557-0-AVaVwCbJl74DGQI4dN/0o5hwRlnfJI3b7v2AfMQBGyyGHO4oyU/zNjScN1y0/OklZHWT/kdQAKmF+D/Y6a3gRQOH+FWgIWO/LhdknTkVnQdScVPbMkqQhI/iFyij0Q7ksyaQc7foBiCBBjaK7s8tY3JxrXJuOQELb8/lZlU0NtbE20+VAw4CQUBfisq8RDTfZw==',
    'st': 'bf5b4b3c006914f9e88181f3a71932f4c36d0b40aa2797d366a88c8547d257c5b700d100b80480ac79be07bed7bedf175bac1484555dc92b8',
    'xsrf-token': 'd80f756ad9b94f07e80ba411d189634e0936d669',
    'acc_type': 'bireysel_uye',
    'kno': 'au-2PSNL-RyqxdkRgiodXVQ',
    'ulfuid': 'null',
    'gcd': '20221203140607',
    'MDR': '20220927',
    'lastVisit': '20221203',
    'userType': 'yeni_bireysel',
    'shuid': 'cgF8TZBGa0EBMmvEpAdfygQ',
    'dopingPurchase': 'false',
    'getPurchase': 'false',
    'searchType': 'MAP/NAVIGATE/MAP',
    'csid': 'rUTihqk0ETfTmce+CfaXF+QHP1prVVwpbc5TWwQNxLHqAc9kAG6Y+RInt3gVgDuQdH/GdIZWaKRTWfAuMmAd8hqDAD/59+I/tE/6K46+zk0yE/WrtzMeJ+L1lFbKH3MRkkleD20LkztLDeIklVdy8uL87D9xfimNTwmMhSItA4X5JaJFKJMbdnBFN6wN3i+b',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Dec+03+2022+14%3A16%3A43+GMT%2B0300+(GMT%2B03%3A00)&version=6.22.0&isIABGlobal=false&hosts=&consentId=68c682a3-0720-439a-9df9-2cc4123e37f9&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0&geolocation=%3B&AwaitingReconsent=false',
    '_ga_CVPS3GXE1Z': 'GS1.1.1670065555.76.1.1670066205.56.0.0',
    '_ga': 'GA1.1.1285305536.1668539579',
}
HEADERS = {
    'authority': 'www.sahibinden.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}


def save_data(data: dict) -> None:
    file_name = datetime.now().strftime('%y%m%d%H%M') + '.json'
    with open(file_name, 'w') as file:
        json.dump(data, file)


def create_models_from_data(data: list[dict]) -> list[Ad]:
    return [
        Ad(**row)
        for row in data['classifiedMarkers']
        if not (int(row['id']) < 1000000000 and not row['thumbnailUrl'])
    ]


def get_data_with_selenium(**url_params: Any) -> list[dict]:
    link = SAHIBINDEN_HOST + '?' + urlencode({**SAHIBINDEN_DEFAULT_PARAMS, **url_params}) + '&m%3AincludeProjectSummaryFields=true'

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
    driver.get(link)
    html = driver.page_source
    data = json.loads(re.sub(r'(\<([^>]+)>)', '', html))
    sleep(4)
    driver.close()
    driver.quit()
    return data


def get_data_with_cookies() -> list[dict]:
    response = requests.get(
        url=SAHIBINDEN_HOST,
        params=SAHIBINDEN_DEFAULT_PARAMS,
        cookies=COOKIES,
        headers=HEADERS,
    )
    print(response.status_code)
    data = response.json()
    return data
