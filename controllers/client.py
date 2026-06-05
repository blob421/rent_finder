from bs4 import BeautifulSoup
import aiohttp
import json
import asyncio
from utils.fetch_w_curl import fetch_with_curl
from utils.db_calls import storelinks, get_links, mark_valid, storeFullData
from utils.validate import url_valid, parse_json, extractRootJson, hasStructureChanged, parseLesPacs
import random
import logging
import os

########################## LOGGING ###############################
current_dir = os.path.dirname(__file__)
log_path = os.path.abspath(os.path.join(current_dir, '../rent_finder.log'))
logger = logging.getLogger(__name__)
logging.basicConfig(filename='rent_finder.log', level=logging.INFO)

###################################################################
FETCH_METHODS = {
    "LogisQuebec": "curl",
    "LesPacs": "browser",
    "rentals": "browser",
    "Louer": "browser",
    "Kijiji": "aiohttp",
    "GestiPro": "aiohttp",
    "RoomLala": "aiohttp",
    "DuProprio": "aiohttp"
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
        for n in range(4):

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
                     {'source': 'rentals', 'limit': 2, 'urls': [f'https://rentals.ca/quebec-city/under-1000?p={n + 1}']}]
            
           
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

            else:
                soup = BeautifulSoup(result, 'html.parser')        
                urls = self.get_hrefs(soup, source)

            if urls:                 
                return await storelinks(urls, source)
           
                
            return 0
        
        else:
            if not result: logger.warning(f'No result from {source} in save link')

            if result :
                for obj in result:
    
                    if not obj.get('url'): continue
                
                    valid = self.validate(source, obj.get('address', None), obj.get('price', None))
                
                
                    obj['valid'] = True if valid else False
                            

                return await storeFullData(obj, source)
            
            return 0

        
     
      

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
        valid = False
        if address:
            if (self.config.get('keyword') in address.lower() 
                                           or self.config.get('postal_code') in address.lower()
                                           or self.config.get('p_alt') in address.lower()):
                valid = True

        if description:

            if (self.config.get('keyword') in description.lower()
                                           or self.config.get('postal_code') in description.lower()
                                           or self.config.get('p_alt') in description.lower()):
                valid = True

        if price and int(price) > self.config.get('max_price'):
                
                valid = False

        if valid:
             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
             print(f'\nFound a valid appartment !, Source: {source} , Price: {price}')
             print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

             self.notifier.send('Found an appartment !', f"""Source: {source}, 
                                                             Price: {price}$""")

        return valid
            
 
      
    async def test_site(self):
        await self.browser.start_alt()
        url = f'https://www.lespac.com/search/results?keywords=logement&geographicAreaId=15769&latitude=46.870284000000005&longitude=-71.36330700000018&cityLocation=true&categoryId=457'

        html = await self.browser.getPageHtml(url, 'LesPacs')
        soup = BeautifulSoup(html, 'html.parser')
        anch = soup.find_all('a', class_="MuiButtonBase-root")
        print(len(anch))
      

        #print([a.get('href') for a in anch])
        await self.browser.stop_alt()





