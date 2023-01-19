import pandas as pd
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
import pandas as pd
import datetime
from soup import get_soup, get_soup_local
import os
from dotenv import load_dotenv

load_dotenv()
ebayAppID = os.getenv('EBAY_APP_ID')
ebayDevID = os.getenv('EBAY_DEV_ID')
ebayCertID = os.getenv('EBAY_CERT_ID')

class Sale:
    def __init__(self, date: datetime.datetime, price: float, url: str):
        self.date = date
        self.price = price
        self.url = url

# list of words to avoid returning slabs
banned_words = ['PSA', 'CGC', 'BGS', 'Beckett', 'AGS']

def get_ebay_sales(search, must_include):
    searchterm = search.replace(' ', '+')
    url = f'https://www.ebay.com/sch/i.html?_from=R40&_nkw={searchterm}&_sacat=0&LH_PrefLoc=1&LH_Sold=1&LH_Complete=1&rt=nc&LH_All=1'
    soup = get_soup(url)

    sales = []

    listings = soup.find_all(class_='s-item__info clearfix')
    for listing in listings:
        name = listing.find(class_='s-item__title').text
        match = True
        print(name)

        for phrase in must_include:
            if phrase.lower() not in name.lower():
                print('bonk by name')
                match = False

        
        for phrase in banned_words:
            if phrase in name:
                print('bonk by ban')
                match = False

        if match:
            details = listing.find_all(class_='s-item__detail s-item__detail--primary')
            price = details[0].text.split('$')
            if len(price) > 1:
                price = price[1]
            else:
                price = price[0]

            shipping = details[2].text
            if shipping.strip() == 'Free shipping':
                shipping = 0
            else:
                shipping = shipping.split('$')
                if len(shipping) > 1:
                    shipping = shipping[1]
                else:
                    shipping = shipping[0]
                shipping = shipping.split(' ')[0]

            date = listing.text.split('Sold ')
            if len(date) > 1:
                date = date[1][1:].strip()
                date = datetime.datetime.strptime(date, '%b %d, %Y')

            details = listing.find('a', href=True)
            listing_url = details['href']

            try:
                sales += [Sale(date, float(price) + float(shipping), listing_url)]
            except Exception as e:
                print(e)
                print(f'{price} or {shipping} is not convertable, date is {date}')
    
    return sales

pd.set_option('display.max_rows', 500)

def get_results(payload):
    try:
        api = Finding(appid = ebayAppID, config_file=None)
        response = api.execute('findItemsAdvanced', payload)
        return response.dict()
    except ConnectionError as e:
        print(e)
        print(e.response.dict())

payload = {
        'keywords': 'sobble sv025', 
        'itemFilter': [
            {'name': 'LocatedIn', 'value': 'US'},
            {'name': 'ListingType', 'value': 'FixedPrice'}
        ],
        'sortOrder': 'PricePlusShippingLowest',
}

# results = get_results(payload)

def get_total_pages(results):
    '''Get the total number of pages from the results'''
    if results:
        return int(results.get('paginationOutput').get('totalPages'))
    else:
        return

def search_ebay(payload):
    '''parse the response - results and concatentate to the dataframe'''
    results = get_results(payload)
    total_pages = get_total_pages(results)
    items_list = results['searchResult']['item']
        
    i = 2
    while(i <= total_pages):
        payload['paginationInput'] = {'entriesPerPage': 100, 'pageNumber': i}        
        results = get_results(payload)
        items_list.extend(results['searchResult']['item'])
        i += 1
        
    df_items = pd.DataFrame(columns=['itemId', 'title', 'priceWithShipping'])

    for item in items_list:
        if item.get('shippingInfo').get('shippingServiceCost'):
            row = {
                'itemId': item.get('itemId'),
                'title': item.get('title'),
                'priceWithShipping': float(item.get('sellingStatus').get('currentPrice').get('value')) + float(item.get('shippingInfo').get('shippingServiceCost').get('value'))
            }

            ## Deprecation note - don't use append
            '''https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.append.html'''
            
            new_df = pd.DataFrame([row])
            df_items = pd.concat([df_items, new_df],axis=0, ignore_index=True)


    return df_items

# df = search_ebay(payload)
# print(df)