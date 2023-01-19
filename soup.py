from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from bs4 import BeautifulSoup
import time
import aiohttp as aiohttp
import random
from proxy_bank import proxy_bank

def get_soup(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = '/app/.apt/usr/bin/google-chrome'
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--referrer=https://www.google.com/')

    proxy_ip = random.choice(proxy_bank)
    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_ip,
        'ftpProxy': proxy_ip,
        'sslProxy': proxy_ip,
        'noProxy': ''
    })
    driver = webdriver.Chrome(executable_path='/app/.chromedriver/bin/chromedriver', chrome_options=chrome_options, service_args=['--proxy-server={0}'.format(proxy_ip)])
    driver.proxy = proxy

    driver.get(url)
    time.sleep(5 + random.randint(0, 3))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    driver.quit()
    return soup

def get_soup_local(url):
    driver = webdriver.Chrome()

    driver.get(url)
    time.sleep(10 + random.randint(0, 3))

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    driver.quit()
    return soup