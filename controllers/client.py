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
class ClientMain:
    def __init__(self, client, notifier, browser):
        self.session = client
        self.notifier = notifier
        self.browser = browser
   
    @staticmethod
    def use_session(fn):
        async def wrapper(self, *args, **kwargs):
      
                try:
                   return await fn(self, *args, **kwargs)
                
                except aiohttp.ClientError as e:
                    print(f'{kwargs.get("err_str")} {e}')

        return wrapper
            
############################### FETCH LINKS AND SAVE ############################################
    @use_session
    async def fetch_links(self, err_str='Error fetching links'):
        await self.browser.start_alt() ## start playwright
        self.browser.start()

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
                     
                     {'source': 'Centris', 'limit': 0, 'urls': ['https://www.centris.ca/fr/propriete~a-louer?sort=None&sortSeed=1450136492&pageSize=20&q=H4sIAAAAAAAACo2PzU_CQBDF_xWyJ016aEz8wBvBjxiNUSF4EA5D95VO2Hbr7hZtCP-7U5BYQRNu8978ZubNUuXGq0sVq0hNnZ3D9a2GGKJtmnKCe9QbWXncws4clVk9yKiEzMWR8k05YnyIfJuIBrkke6T8e0vKJsA1zaXKKSTZsC6bVp9DfcU-OE6CYAGfQdxXFJrmEIO1yJOLc7WK_h_sGfMz-1yNqzi-7k6RdI6GtvIdA98h52yh2XvkKII_3q4-UytJmzKM9iMyFTYR18ad3g-4aJhWpL_BTaAtKzd-kxQws65uIS_wrCUYk9mBBzCGi9n66zZfhB3wgRfC9RyoxQ3eK3K4AfZoKvShbHPsSd5qB4gPYLqnQk1WX8tKpwVdAgAA&v=2&view=Thumbnail']},
                     {'source': 'Louer', 'limit': 3 , 'urls': [f'https://louer.ca/quebec-city?types=tous-les-appartements&types=chambres&prix-min=0&prix-max=1000&p={n + 1}']},
                     {'source': 'RoomLala', 'limit': 2, 'urls': [f'https://fr.roomlala.ca/chambre-a-louer/wendake-795313/{n + 1}?nightRateMax=80&monthRateMax=800']},
                     {'source': 'rentals', 'limit': 2, 'urls': [f'https://rentals.ca/quebec-city/under-1000?p={n + 1}']}]
            
                
            
    

            for obj in urls:

                if n + 1 > obj.get('limit'): continue

                await asyncio.sleep(random.uniform(1, 2.5)) 
                source = obj['source']
                for url in obj['urls']:
                    hrefs = None
                 

                    if source == 'LogisQuebec':
                        text_data = await fetch_with_curl(url)

                    elif source == 'LesPacs':
                        text_data = await self.browser.getPageHtml(url, source)

                
                    elif source == 'Louer':
                        hrefs = await self.browser.getPageHtml(url, source)

                        if not hrefs:
                            continue

                    elif source == 'rentals':
                        
                        text_data =  await self.browser.getPageHtml(url, source)

                        if not text_data:
                            continue
                    
                    else:
                        response = await self.session.get(url)

                        if not response.ok:
                        
                            text_data = await fetch_with_curl(url)
                        
                        else:
                            
                            text_data = await response.text()

                 
               
                    await self.save_links(text_data, source, hrefs)
                
        await self.browser.stop_alt() ### Stop playwright
        self.browser.stop()

    async def save_links(self, data, source, full_data=None):

        if source == 'RoomLala':
            
            urls = extractRootJson(data, source)
            if urls:
                await storelinks(urls, source)
             
        
        elif not full_data:
            soup = BeautifulSoup(data, 'html.parser')
            
            if source == 'LesPacs':
                    anchors = soup.find_all('a', class_="MuiButtonBase-root")
            else:
                anchors = soup.find_all('a')


            listings = [a.get('href') for a in anchors if a.get('href') and url_valid(a.get('href'), source)]

            if source == 'LogisQuebec':
            
                listings = ['https://www.logisquebec.com' + u for u in listings]
            
      
            if listings:
            
            
                await storelinks(listings, source)
        else:
       
            for obj in full_data:
 
                if not obj.get('url'): continue
             
                valid = self.validate(source, obj.get('address', None), obj.get('price', None))
            
             
                obj['valid'] = True if valid else False
                          
        

            await storeFullData(obj, source)
     
      

#################### RETRIEVING AND FILTERING #######################################################
    

    @use_session
    async def get_page(self, url, err_str='Failed to get a single page'):
        response=  await self.session.get(url) 
        if not response.ok:
              text_data = await fetch_with_curl(url)
        else:
              text_data = await response.text()
        return text_data

    
    async def filterLinks(self):
        links = await get_links()       ### ALL links that are not checked 
       
        if links:
            playwright_started = False

            for obj in links:
                l = obj[0]
                source = obj[3]

                await asyncio.sleep(random.uniform(2.5, 6.0))  ### Human like behavior
                valid = False
                

                if source in ['rentals', 'LesPacs']: 
                    if not playwright_started:
                        await self.browser.start_alt() ## start playwright
                        playwright_started = True
                  
                    data = await self.browser.getPageHtml(l, source)

                else:
                    data = await self.get_page(l)

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

            if playwright_started:
                await self.browser.stop_alt()
        
                        
    async def test_site(self):
        await self.browser.start_alt()
        url = f'https://www.lespac.com/search/results?keywords=logement&geographicAreaId=15769&latitude=46.870284000000005&longitude=-71.36330700000018&cityLocation=true&categoryId=457'

        html = await self.browser.getPageHtml(url, 'LesPacs')
        soup = BeautifulSoup(html, 'html.parser')
        anch = soup.find_all('a', class_="MuiButtonBase-root")
        print(len(anch))
      

        #print([a.get('href') for a in anch])
        await self.browser.stop_alt()
       

    def validate(self, source, address, price, description=None):
        valid = False
        if address:
            if 'wendake' in address.lower() or 'g0a' in address.lower():
                valid = True

        if description and 'wendake' in description.lower():
                valid = True

        if price and int(price) > 950:
                valid = False

        if valid:
             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
             print(f'\nFound a valid appartment !, Source: {source} , Price: {price}')
             print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

             self.notifier.send('Found an appartment !', f"""Source: {source}, 
                                                             Price: {price}$""")

        return valid
            
 
      






