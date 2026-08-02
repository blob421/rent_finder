from bs4 import BeautifulSoup
import aiohttp
import json
import asyncio
from utils.fetch_w_curl import fetch_with_curl
from utils.db_calls import storelinks, get_links, mark_valid, storeFullData, isUrl
from utils.validate import url_valid, parse_json, extractRootJson, hasStructureChanged, parseLesPacs
import random
import logging
import os

########################## LOGGING ###############################
current_dir = os.path.dirname(__file__)
log_path = os.path.abspath(os.path.join(current_dir, '../rent_finder.log'))
logger = logging.getLogger(__name__)
logging.basicConfig(filename=log_path, level=logging.INFO)

###################################################################
FETCH_METHODS = {
    "LogisQuebec": "curl",
    "LesPacs": "browser",
    "rentals": "browser",
    "Louer": "browser",
    "Kijiji": "aiohttp",
    "GestiPro": "aiohttp",
    "RoomLala": "aiohttp",
    "DuProprio": "aiohttp",
    "Rentola": 'aiohttp'
}

class ClientMain:
    def __init__(self, client, notifier, browser, config):
        self.session = client
        self.notifier = notifier
        self.browser = browser
        self.config = config
   
    @staticmethod
    def use_session(fn):
        async def wrapper(self, *args, **kwargs):
                try:
                   return await fn(self, *args, **kwargs)
                
                except (Exception, aiohttp.ClientError) as e:
                    print(f'{kwargs.get("err_str")} {e}')

        return wrapper
    
    @staticmethod
    def use_browser(fn):
        async def wrapper(self, *args, **kwargs):
            try:
                await self.browser.start_alt() ## start playwright
                result = await fn(self, *args, **kwargs)
                return result
            
            except Exception as e:
                print(f'Error with the fetch_links function : {e}')

            finally:
                await self.browser.stop_alt() ### Stop playwright
           

        return wrapper

############################### FETCH LINKS AND SAVE ############################################
    @use_browser
    async def fetch_links(self, constraint=None):
        error_string = 'Error fetching links from : '
        new_urls_total = 0
        for n in range(10):

            urls = [{'source': 'Kijiji', 'limit': 4,
                     'urls': [f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/logement/page-{n+1}/k0c30349001l1700121?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list',
                              f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/chambre/page-{n+1}/k0c30349001l1700124?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list']
                      },
                      {'source': 'LogisQuebec', 'limit': 2, 
                     'urls': [f'https://www.logisquebec.com/result-search/?source=a_louer&query=Wendake&lq-query=Wendake&type=&room=0&prix_min=0&prix_max=999999999&region=13&ville=1716&tri=1&page={n + 1}']},
                 
                    {'source': 'LesPacs', 'limit': 2, 
                     'urls': [f'https://www.lespac.com/en/wendake/logement_b457g15769k{n+1}R1.jsa?ncc=dx0e46P870284000000005fM71P36330700000018h0i1irZ006dHJ1ZQis20j0']},
                     {'source': 'DuProprio', 'limit': 1, 'urls': ['https://duproprio.com/fr/location/quebec-rive-nord/wendake']},
                     
                     {'source': 'GestiPro', 'limit' : 2, 'urls': [f'https://gestipro.info/resultats/page/{n+1}/?areas%5B0%5D=quebec&animaux&max-price=1000']},
                     
                     {'source': 'Louer', 'limit': 3 , 'urls': [f'https://louer.ca/quebec-city?types=tous-les-appartements&types=chambres&prix-min=0&prix-max=1000&p={n + 1}']},
                     {'source': 'RoomLala', 'limit': 2, 'urls': [f'https://fr.roomlala.ca/chambre-a-louer/wendake-795313/{n + 1}?nightRateMax=80&monthRateMax=800']},
                     {'source': 'rentals', 'limit': 2, 'urls': [f'https://rentals.ca/quebec-city/under-1000?p={n + 1}']},
                     {'source': 'Rentola', 'limit': 11, 'urls': [f'https://rentola.ca/for-rent?location=quebec&order=desc&property_types=room&property_types=apartment&property_types=studio&property_types=student-apartment&rent=0-1000&page={n + 1}']}]
            
           
            for obj in urls:
               

                if n + 1 > obj.get('limit'): continue

                await asyncio.sleep(random.uniform(1, 2.5)) 
                source = obj['source']

                if constraint and constraint != source: continue
               
                tasks = [self.get_page(u, source, err_str=f'{error_string} {source}') for u in obj['urls']]
                results = await asyncio.gather(*tasks)
                
                for r in results:
               
                    if r.get('type') == 'error': 
                        err_str = f'There was an error fetching a link from: {source}'
                        print(err_str) 
                        logger.info(err_str)   
                        continue

                    new_urls_total += await self.save_links(r, source)

        return new_urls_total
                

    async def save_links(self, data, source):
        data_type = data.get('type')
        result = data.get('result')
        
 
        if data_type == 'page':
            urls = None
            if source == 'RoomLala':
                urls = extractRootJson(result, source)

            elif source == 'Rentola':
               dataset = await self.getFullData(source, result)
               if dataset:
                    count = 0
                    for d in dataset:
                        if not await isUrl(url=d.get('url')):
                            valid = self.validate(source, d.get('address', None), d.get('price', None))
                            d['valid'] = valid
                            count += await storeFullData(d, source)

                    return count
             

            else:
                soup = BeautifulSoup(result, 'html.parser')        
                urls = self.get_hrefs(soup, source)

            if urls:                 
                return await storelinks(urls, source)
           
                
            return 0
        
        else:
            if not result: logger.warning(f'No result from {source} in save link')
            url_count = 0
            if result :
                
                for obj in result:
     
                    if not obj.get('url'): continue

                    if not await isUrl(url=obj.get('url')):

                        valid = self.validate(source, obj.get('address', None), obj.get('price', None))
                    
                    
                        obj['valid'] = True if valid else False
                            

                        url_count += await storeFullData(obj, source)
            
            return url_count

        
     
      

#################### RETRIEVING AND FILTERING #######################################################
    def get_hrefs(self, soup, source):
        if soup:

            if source == 'LesPacs':                       
                anchors = soup.find_all('a', class_="MuiButtonBase-root")
                
            else:
                anchors = soup.find_all('a')

            listings = [a.get('href') for a in anchors if a.get('href') and url_valid(a.get('href'), source)]

            if source == 'LogisQuebec':
            
                listings = ['https://www.logisquebec.com' + u for u in listings]

            return listings 
        
        return None


    @use_session
    async def get_page(self, url, source, err_str='Error fetching page content'):

        result = None
        method = FETCH_METHODS.get(source)

        if method == 'curl':  
            result = await fetch_with_curl(url)

        elif method == 'browser':
            result = await self.browser.getPageHtml(url, source)
     
        elif method == 'aiohttp':
          
            response = await self.session.get(url) 
            if response.ok:
                text_data = await response.text()
                result = {'result': text_data, 'type': 'page'}
    

        return result if result else {'result': None, 'type': 'error'}
       
    

    async def process_links(self):
        links = await get_links()       ### ALL links that are not checked 
       
        if links:
            playwright_started = False

            for obj in links:
                l = obj[0]
                source = obj[3]

                if not playwright_started and FETCH_METHODS.get(source) == 'browser': 
                    await self.browser.start_alt() ## start playwright
                    playwright_started = True
                
                result = await self.get_page(l, source, err_str=f'Error processing link from : {source}')

                if result.get('type') == 'error': continue

                data = result.get('result')
             

                await self.parse_and_validate(source, l , data)

                await asyncio.sleep(random.uniform(2.5, 6.0))  ### Human like behavior


            if playwright_started:
                await self.browser.stop_alt()
        
    async def parse_and_validate(self, source, l, data):
        valid = False
        
        if source == 'LesPacs':
            address, price, description = parseLesPacs(data)

        else:
            soup = BeautifulSoup(data, 'html.parser')
            scripts = soup.find_all("script", {"type": "application/ld+json"}) 

            price = None
            address = None
            description = None
            valid = False

            for s in scripts:
                data = s.string
                parsed = json.loads(data)
                result = parse_json(parsed, source)

                if result:                 
                    price = result.get('price') or price
                    address = result.get('address') or address
                    description = result.get('description') or description

                
            if source == 'GestiPro' and not price:
                pricetag = soup.find('span', {'class': 'price'})
                if pricetag:
                    price = pricetag.get_text(strip=True).replace('$', '').replace(',', '')

        hasStructureChanged(source, {'price': price, 'description': description, 'address': address})

        valid = self.validate(source, address, price, description)
        await mark_valid({'url':l, 'price': price, 'valid': valid})



       
    def validate(self, source, address, price, description=None):
        valid = True
        keyword = self.config.get('keyword', None)
        pc = self.config.get('postal_code', None)
        notable = False

        if keyword and pc:
            
            if address:
                if (keyword in address.lower() 
                                            or pc in address.lower()
                                            or self.config.get('p_alt') in address.lower()):
                    valid = True
                    notable = True

            if description:

                if (keyword in description.lower()
                                            or pc in description.lower()
                                            or self.config.get('p_alt') in description.lower()):
                    valid = True
                    notable = True

        if price and (int(price) > self.config.get('max_price') 
                       or int(price) < self.config.get('min_price')):
                
                valid = False

        if valid:
             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
             print(f'\nFound a valid appartment !, Source: {source} , Price: {price}')
             print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

             if not notable:
                 self.notifier.send('Range match !', f"""Source: {source}, 
                                                                 Price: {price}$""")
             else:
                 self.notifier.send('LUCKY FIND !!', f"""Source: {source}, 
                                                         Price: {price}$""")

        return valid
            
 
    async def getFullData(self, source, html):
        dataset = []
        soup = BeautifulSoup(html, 'html.parser')
        if source == 'Rentola':
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for s in scripts:
            
                text = s.string
                parsed = json.loads(text)
                if parsed.get('@type') == 'SearchResultsPage':
                
                    listings = parsed.get('mainEntity', {}).get('itemListElement', [])
                    if listings:
                        for e in listings:
                            if e.get('@type') == 'ListItem':
                                item = e.get('item', {})

                                url = item.get('url', None)
                                offers = item.get('offers', {})

                                price = offers.get('price', None)  
                                address = offers.get('itemOffered', {}).get("address", {}).get('streetAddress', None)
        
                                dataset.append({'url': url, 'price': price, 'address': address})
        return dataset  



    async def test_site(self):
       
        url = f'https://rentola.ca/for-rent?location=quebec&order=desc&property_types=room&property_types=apartment&property_types=studio&property_types=student-apartment&rent=0-1000&page=1'
        dataset = []
        resp = await self.session.get(url)
        html = await resp.text()
       
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for s in scripts:
         
            text = s.string
            parsed = json.loads(text)
            if parsed.get('@type') == 'SearchResultsPage':
             
                listings = parsed.get('mainEntity', {}).get('itemListElement', [])
                if listings:
                    for e in listings:
                        if e.get('@type') == 'ListItem':
                            item = e.get('item', {})

                            url = item.get('url', None)
                            offers = item.get('offers', {})

                            price = offers.get('price', None)  
                            address = offers.get('itemOffered', {}).get("address", {}).get('streetAddress', None)
      
                            dataset.append({'url': url, 'price': price, 'address': address})
        return dataset
       





