import gspread
from gspread_formatting import DataValidationRule, BooleanCondition, set_data_validation_for_cell_range
import discord
import aiohttp as aiohttp
import datetime
from ebay import get_ebay_sales, Sale
from soup import get_soup, get_soup_local

class Result:
    def __init__(self, jp, image, name, must_include, market, low):
        self.image = image
        self.name = name
        self.market = market
        self.low = low
        self.tcg_product_url = ''
        self.dates = []
        self.sales = []
        self.max = 0
        self.min = 0
        self.avg_days = 0
        self.avg_price = 0
        self.jp = jp
        self.must_include = must_include
        self.number = ''
        self.link = ''
    
    def filter(self):
        for phrase in self.must_include:
            if phrase.lower() not in self.name.lower() and phrase.lower() not in self.number:
                return False
        return True

    def get_sales(self):
        if self.jp == False:
            soup = get_soup(self.tcg_product_url)
            sales_elem = soup.find(class_='latest-sales price-guide__latest-sales')
            if sales_elem.find(class_='frosted'):
                print('not enough data')
                return
            sales = sales_elem.find_all('li')
            for sale in sales:
                if sale.find(class_='condition').get_text().strip() == 'NM':
                    date = sale.find(class_='date').get_text().strip()
                    date = datetime.datetime.strptime(date, '%m/%d/%y')
                    self.dates += [date]
                    self.sales += [Sale(date, float(sale.find(class_='price').get_text().split('$')[1]), self.tcg_product_url)]
        ebay_sales = get_ebay_sales(f'{self.name} {self.number}', self.must_include)
        self.dates += [sale.date for sale in ebay_sales]
        self.sales += ebay_sales
        print(f'here are the sales: {self.sales}')
        

async def tcgp(name, must_include = ''):
    url = 'https://www.tcgplayer.com/search/all/product?q=' + name.replace(' ', '+') + '&view=grid'
    soup = get_soup(url)

    reply = []
    cards = []

    results = soup.find_all(class_='search-result__content')
    for result in results:
        img_elem = result.find('img')
        img_url = img_elem.get('src')
        name = result.find(class_='search-result__title').get_text()
        market_elem = result.find(class_='search-result__market-price--value')
        if market_elem:
            market = market_elem.get_text()
        else:
            market = "not available"
        low_elem = result.find(class_='inventory__price-with-shipping')
        if low_elem:
            low = low_elem.get_text()
        else:
            low = "not available"
        details = result.find('a', href=True)
        details_url = 'https://www.tcgplayer.com' + details['href']
        
        r = Result(False, img_url, name, must_include, market, low)

        r.tcg_product_url = details_url
        r.link = details_url
        rarity = result.find(class_='search-result__rarity')
        r.number = rarity.find_all('span')[2].get_text().strip('#')

        cards += [r]
    
    # filter results
    for card in cards:
        if card.filter():
            reply += [card]

    return reply

async def tcgr(name, must_include = '', category = ''):
    if category.lower() == 'weiss':
        url = 'https://tcgrepublic.com/product/text_search.html?category=31&q=' + name.replace(' ', '%20')
    elif category.lower() == 'pokemon':
        url = 'https://tcgrepublic.com/product/text_search.html?category=35&q=' + name.replace(' ', '%20')
    else:
        url = 'https://tcgrepublic.com/product/text_search.html?q=' + name.replace(' ', '+')
    soup = get_soup(url)

    reply = []
    cards = []

    results = soup.find_all(class_='product_thumbnail')
    for result in results:
        img_elem = result.find('img')
        img_url = 'https://tcgrepublic.com' + img_elem.get('src')
        name = result.find(class_='product_thumbnail_caption').get_text().strip('\n')
        market_elem = result.find(class_='price_color_thumb')
        if market_elem:
            market = market_elem.get_text()
        else:
            market = "not available"
        low = "---"
        cards += [Result(True, img_url, name, must_include, market, low)]
    
    # filter results
    for card in cards:
        if card.filter():
            reply += [card]

    return reply

async def spreadsheet():
    sa = gspread.service_account(filename="googlesheetscredentialsfile.json")
    sh = sa.open("sobble shareables")
    wks = sh.worksheet("Price Lookup")
    names = wks.get('A:A')
    keywords = wks.get('B:B')
    jp = wks.get('C:C')
            
    for i in range(len(names) - 1):
        if not names[i+1]:
            continue
        if keywords[i+1]:
            must_include = keywords[i+1][0].split(', ')
        else:
            must_include = []
        if jp[i+1] == ['TRUE']:
            print(f'calling tcgr with arguments {names[i+1][0]} and {must_include}')
            results = await tcgr(names[i+1][0], must_include)
            for result in results:
                result.jp = True
        else:
            print(f'calling tcgp with arguments {names[i+1][0]} and {must_include}')
            results = await tcgp(names[i+1][0], must_include)
        if len(results) == 0:
            wks.update('D{0}'.format(i + 2), "no results")
            wks.update('E{0}'.format(i + 2), "no results")
            wks.update('F{0}'.format(i + 2), "no results")
        else:
            if len(results) > 1:
                wks.format(f'D{i+2}', {
                    "backgroundColor": {
                        "red": 1.0,
                        "green": 0.9,
                        "blue": 0.3
                    }
                })
            result = results[0]
            result.get_sales()
            result.sales.sort(key = lambda x: x.date, reverse = True)
            if len(result.sales) > 6:
                result.sales = result.sales[:6]
            delta = result.sales[0].date - result.sales[-1].date
            result.avg_days = delta.days/len(result.sales)
            result.avg_price = sum([sale.price for sale in result.sales])/len(result.sales)
            result.max = max([sale.price for sale in result.sales])
            result.min = min([sale.price for sale in result.sales])
            
            wks.update(f'D{i + 2}', result.name)
            wks.update(f'E{i + 2}', result.market)
            wks.update(f'F{i + 2}', result.low)
            sparkline = '=SPARKLINE({{' + 'AA{0};X{0};U{0};R{0};O{0};L{0}'.format(i + 2) + '},{' + 'AB{0};Y{0};V{0};S{0};P{0};M{0}'.format(i + 2) + '}})'
            wks.update(f'G{i + 2}', [[sparkline]], value_input_option='USER_ENTERED')
            wks.update(f'H{i + 2}:K{i + 2}', [[result.min, result.max, result.avg_price, result.avg_days]])
            sales_list = []
            for sale in result.sales:
                sales_list += [sale.date.strftime('%m/%d/%y'), sale.price, sale.url]
            wks.update(f'L{i + 2}:AC{i + 2}', [sales_list], raw=False)
            

async def resetSpreadsheet():
    sa = gspread.service_account(filename="googlesheetscredentialsfile.json")
    sh = sa.open("sobble shareables")
    wks = sh.worksheet("Price Lookup")
    wks.clear()
    wks.format('A2:V100', {
        "background_color": {
            "red": 1.0,
            "blue": 1.0,
            "green": 1.0
        }
    })
    ranges = ['L1:N1', 'O1:Q1', 'R1:T1', 'U1:W1', 'X1:Z1', 'AA1:AC1']
    colors = [{"red": 0, "blue": 0.8, "green": 0.8}, {"red": 0.7, "blue": 0.0, "green": 0.4}, {"red": 0.7, "blue": 0.8, "green": 0.6}, {"red": 0.6, "blue": 0.1, "green": 0.6}, {"red": 0.4, "blue": 0.8, "green": 0.3}, {"red": 0.6, "blue": 0.6, "green": 0.7}]
    for i in range(len(ranges)):
        wks.format(ranges[i], {
            "background_color": colors[i]
        })
    validation_rule = DataValidationRule(
            BooleanCondition('BOOLEAN', ['TRUE', 'FALSE']),
            showCustomUi=True)
    set_data_validation_for_cell_range(wks, 'C2:C999', validation_rule)
    wks.update('B1000:C1000', [['.', '.']])
    wks.update('A1:AC1', [['search', 'keywords', 'japanese?', 'result name', 'market', 'low listing', 'trend', 'min', 'max', 'avg sale price', 'avg days for sale', 'date', 'sale', 'link', 'date', 'sale', 'link', 'date', 'sale', 'link', 'date', 'sale', 'link', 'date', 'sale', 'link', 'date', 'sale', 'link']])

async def spreadsheetInput():
    sa = gspread.service_account(filename="googlesheetscredentialsfile.json")
    sh = sa.open("sobble shareables")
    wks = sh.worksheet("Buddies With Benefits")
    for letter in ['A', 'B', 'C', 'D', 'E']:
        data = wks.get(f'{letter}:{letter}')
        print(f'column {letter} has the data {data}')

async def tcgpEmbed(search, must_include = ""):
    max_results_shown = 5
    
    results = await tcgp(search, must_include)
    embeds = []
    for i in range(min(len(results), max_results_shown)):
        embed = discord.Embed(title = results[i].name)
        embed.set_thumbnail(url = results[i].image)
        embed.add_field(name = "market price", value = results[i].market, inline = True)
        embed.add_field(name = "lowest listing", value = results[i].low, inline = True)
        embeds += [embed]
    return embeds

async def tcgrEmbed(search, must_include = "", category = ""):
    max_results_shown = 5

    results = await tcgr(search, must_include, category)
    embeds = []
    for i in range(min(len(results), max_results_shown)):
        embed = discord.Embed(title = results[i].name)
        embed.set_thumbnail(url = results[i].image)
        embed.add_field(name = "market price", value = results[i].market, inline = True)
        embed.add_field(name = "lowest listing", value = results[i].low, inline = True)
        embeds += [embed]
    return embeds