import json
import re
from datetime import datetime
from random import shuffle
from time import sleep
from typing import Any
from urllib.parse import urlencode

import requests
from pyquery import PyQuery
from selenium import webdriver

from config import mapbox_config


SAHIBINDEN_HOST = "https://www.sahibinden.com"
SAHIBINDEN_HOST_ADS_SUFFIX = "/ajax/mapSearch/classified/markers"
SAHIBINDEN_HOST_AREAS_SUFFIX = "/ajax/location/getDistricts"
SAHIBINDEN_DEFAULT_PARAMS = {
    "address_country": "1",
    "m:includeProjectSummaryFields": "true",
    "language": "en",
    "category": "16624",
    "price_currency": "1",
    "address_city": "7",
    "pagingOffset": "0",

}
VARIABLE_PARAMS = {
    # (1day, 7days, 15days, 30days)
    "date": "30days",
    "price_max": "25000",
}
COOKIES = {
    "vid": "831",
    "cdid": "c50vCHNBN4SzpfX76373e4b9",
    "__ssid": "67ba7120581250b01a5b8d35baab3aa",
    "_gcl_au": "1.1.2131970503.1668539580",
    "OptanonAlertBoxClosed": "2022-11-15T19:14:44.197Z",
    "nwsh": "std",
    "showPremiumBanner": "false",
    "h28s1ZLRQ2": "A9qeoIuEAQAAe_MKN-xHelX9Gcla-syrJUHTFiBKrXp9QQk65Kn-TPNiF-w_AVjoqhuucmW8wH8AADQwAAAAAA|1|0|"
    + "bb001baedb500404d6d7059146f9dabfa9bd1f93",
    "MS1": "https://www.sahibinden.com/ilan/emlak-konut-kiralik-tomas-gayrimenkul-2-plus1-esyali-kiralik-1058997090"
    + "/detay",
    "userLastSearchSplashClosed": "true",
    "acc_type": "bireysel_uye",
    "kno": "au-2PSNL-RyqxdkRgiodXVQ",
    "rememberedUserName": "apaktusov",
    "st": "adc4f2d91e1d146558730dd5f2d18c7e18b71d743c3d068a5627d3d99881f330f1bb256066b283d3b4d0ed782e18c9bbf"
    + "4c5e3c28468f14eb",
    "segIds": "",
    "_gid": "GA1.2.938412405.1671134094",
    "_openContent": "price%2Ca24%2Ca20",
    "geoipCity": "antalya",
    "geoipIsp": "turk_telekom",
    "dp": "1920*1080-landscape",
    "searchType": "MAP/NAVIGATE/MAP",
    "_dc_gtm_UA-235070-1": "1",
    "_gali": "searchResultLeft-mapCTA",
    "csid": "Y6NutT8QbZfEKctRGNJEMMlEUFbbNj9ijUmwhW6TaJ0fWPivhzFu4c0JI4gA4UMlooD8b/86vTcgcLlpy5JZDaqB1RDOfQoyL9etKdV"
    + "MctL7TBrMjoZrfmgZSmJ19uxFkCHeNVuplVE+HvqEibXG37TwyKFZ5u6EFX7jrIhJTkB9GXI+gk41ZSmEJWGrbLIh",
    "_ga": "GA1.1.1285305536.1668539579",
    "_ga_CVPS3GXE1Z": "GS1.1.1671200562.109.1.1671200746.42.0.0",
    "OptanonConsent": "isGpcEnabled=0&datestamp=Fri+Dec+16+2022+17%3A25%3A48+GMT%2B0300+(GMT%2B03%3A00)&"
    + "version=6.22.0&isIABGlobal=false&hosts=&consentId=68c682a3-0720-439a-9df9-2cc4123e37f9&"
    + "interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%"
    + "2CC0004%3A0&geolocation=%3B&AwaitingReconsent=false",
}
HEADERS = {
    "authority": "www.sahibinden.com",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,tr;q=0.6",
    "content-type": "application/json; charset=utf-8",
    "referer": "https://www.sahibinden.com/search-map/en/for-rent-flat/antalya-muratpasa?a24_max=12000&"
    + "autoViewport=3&price_max=12000",
    "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/107.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def save_data(data: dict) -> None:
    file_name = f"{datetime.now():%y%m%d%H%M}.json"
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file)


def get_data_with_selenium(**url_params: Any) -> list[dict]:
    link = SAHIBINDEN_HOST + "?" + urlencode({**SAHIBINDEN_DEFAULT_PARAMS, **url_params})

    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-javascript")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Remote(command_executor="http://selenium:4444/wd/hub", options=options)

    driver.get("https://www.sahibinden.com")
    sleep(4)
    driver.get(link)
    html = driver.page_source
    data = json.loads(re.sub(r"(\<([^>]+)>)", "", html))
    sleep(4)
    driver.close()
    driver.quit()
    return data["classifiedMarkers"]


def get_data_with_cookies(city_params: dict) -> list[dict] | None:
    response = requests.get(
        url=SAHIBINDEN_HOST + SAHIBINDEN_HOST_ADS_SUFFIX,
        params=SAHIBINDEN_DEFAULT_PARAMS | VARIABLE_PARAMS | city_params,
        cookies=COOKIES,
        headers=HEADERS,
        timeout=10,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    return data["classifiedMarkers"]


def get_data_and_photos_ad(url: str) -> (dict | None, list[str] | None):
    response = requests.get(
        url=url,
        cookies=COOKIES,
        headers=HEADERS,
        timeout=10,
    )
    if response.status_code != 200:
        return None, None

    html = PyQuery(response.text)
    customdata = json.loads(html("#gaPageViewTrackingJson").attr("data-json"))
    data = {i["name"]: i["value"] for i in customdata["customVars"]}

    img_links = []
    availabl_megaphotos = "passive" not in html('a:Contains("Mega Photo")').attr("class")
    if availabl_megaphotos:
        for div in html("div.megaPhotoThmbItem"):
            link = PyQuery(div).find("img").attr("data-source")
            if link:
                img_links.append(link)
    else:
        for img in html("div.classifiedDetailMainPhoto").find("img"):
            link = PyQuery(img).attr("data-src")
            if link:
                img_links.append(link)
    shuffle(img_links)
    return data, img_links[:3]


def get_map_image(lat: float, lon: float) -> str | None:
    if not lat or not lon:
        return None
    url = f"{mapbox_config.url}/pin-l+0031f5({lon},{lat})/{lon},{lat},12/1200x600?access_token={mapbox_config.token}"
    return url
