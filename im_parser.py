import time
from selenium import webdriver
import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient()
db = client.igromaster_parser
game_cards = db.game_cards

URL='https://igromaster.by/catalog/romanticheskie/' #13
# URL = 'https://igromaster.by/catalog/kooperativnye/' #163

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'accept':'*/*'
    }

driver = webdriver.Chrome()
driver.get(URL)

game_links = []
games = []

def scroll(driver, timeout):
    # scrolling page to the bottom to have all the game cards loaded
    scroll_pause_time = timeout
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parsing_game_cards():
    scroll(driver, 10)
    driver.implicitly_wait(30)
    game_char_links = driver.find_elements_by_xpath("//div[@class='product-item-title']//a[@href]")
    for link in game_char_links:
        href = link.get_attribute("href")
        game_links.append(href)
    driver.close()
    return game_links

def get_html(url):
    r = requests.get(url, headers=HEADERS)
    return r

def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    characteristics = {}
    chars_block = soup.find_all("div", class_="product-item-detail-properties")
    for char in chars_block:
        key = char.find_next('div', class_="product-item-detail-properties-name").get_text()
        val = char.find_next('div', class_="product-item-detail-properties-val").get_text()
        characteristics[key] = val

    img_urls = []
    images = soup.find_all('div', class_='product-item-detail-slider-controls-image')
    for image in images:
        src = 'https://igromaster.by' + image.find_next('img').get('data-lazyload-src')
        img_urls.append(src)

    desc_img_urls = []
    desc_images = soup.find_all('div', class_='product-item-detail-description')
    for desc_image in desc_images:
        if desc_image.find_next('img').get('data-lazyload-src'):
            src = 'https://igromaster.by' + desc_image.find_next('img').get('data-lazyload-src')
            desc_img_urls.append(src)

    try:
        rating = soup.find('span', class_='product-item-detail-rating-val').get_text()
    except AttributeError:
        rating = 'Рейтинг не указан'

    # price = soup.find('span', class_='product-item-detail-price-current').get_text()
    # price = re.findall(r'\d+', price)
    # price = int(price[0])

    games.append({
        'title': soup.find('h1', class_='navigation-title').get_text(),
        'price': soup.find('span', class_='product-item-detail-price-current').get_text(),
        'rating': rating,
        'description': soup.find('div', class_='product-item-detail-description').get_text(strip=True).replace('Описание', '').replace('\xa0', ' '),
        'description_img': desc_img_urls,
        'characteristics':characteristics,
        'images': img_urls,
    })

    return games

def parse(link):
    html = get_html(link)
    if html.status_code == 200:
        get_content(html.text)
    else:
        print('Error')

if __name__ == '__main__':
    start = time.time()

    parsing_game_cards()
    # get_html(url=URL)
    for link in game_links:
        parse(link)

    for game in games:
        game_cards.insert_one(game)

    end = time.time()

    print(games)
    print(len(games))
    print(f"Runtime of the program is {end - start}")