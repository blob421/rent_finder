from bs4 import BeautifulSoup
import subprocess
import aiohttp
import json
import asyncio
from utils.db_calls import storelinks, get_links, mark_valid, storeFullData
from utils.validate import url_valid, parse_json
import random


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
            
############################### FETCH AND SAVE ############################################
    @use_session
    async def fetch_links(self, err_str='Error fetching links'):
        for n in range(4):
            urls = [{'source': 'Kijiji', 'limit': 4,
                     'urls': [f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/logement/page-{n+1}/k0c30349001l1700121?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list',
                              f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/chambre/page-{n+1}/k0c30349001l1700124?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list']
                      },

                    {'source': 'LogisQuebec', 'limit': 2, 
                     'urls': [f'https://www.logisquebec.com/result-search/?source=a_louer&query=Wendake&lq-query=Wendake&type=&room=0&prix_min=0&prix_max=999999999&region=13&ville=1716&tri=1&page={n + 1}']},
                 
                    {'source': 'LesPacs', 'limit': 0, 
                     'urls': ['https://www.lespac.com/search/results?keywords=logement&geographicAreaId=15769&latitude=46.870284000000005&longitude=-71.36330700000018&cityLocation=true&categoryId=457']},
                     
                     {'source': 'DuProprio', 'limit': 1, 'urls': ['https://duproprio.com/fr/location/quebec-rive-nord/wendake']},
                     
                     {'source': 'GestiPro', 'limit' : 2, 'urls': [f'https://gestipro.info/resultats/page/{n+1}/?areas%5B0%5D=quebec&animaux&max-price=1000']},
                     
                     {'source': 'Centris', 'limit': 0, 'urls': ['https://www.centris.ca/fr/propriete~a-louer?sort=None&sortSeed=1450136492&pageSize=20&q=H4sIAAAAAAAACo2PzU_CQBDF_xWyJ016aEz8wBvBjxiNUSF4EA5D95VO2Hbr7hZtCP-7U5BYQRNu8978ZubNUuXGq0sVq0hNnZ3D9a2GGKJtmnKCe9QbWXncws4clVk9yKiEzMWR8k05YnyIfJuIBrkke6T8e0vKJsA1zaXKKSTZsC6bVp9DfcU-OE6CYAGfQdxXFJrmEIO1yJOLc7WK_h_sGfMz-1yNqzi-7k6RdI6GtvIdA98h52yh2XvkKII_3q4-UytJmzKM9iMyFTYR18ad3g-4aJhWpL_BTaAtKzd-kxQws65uIS_wrCUYk9mBBzCGi9n66zZfhB3wgRfC9RyoxQ3eK3K4AfZoKvShbHPsSd5qB4gPYLqnQk1WX8tKpwVdAgAA&v=2&view=Thumbnail']},
                     {'source': 'Louer', 'limit': 3 , 'urls': [f'https://louer.ca/quebec-city?types=tous-les-appartements&types=chambres&prix-min=0&prix-max=1000&p={n + 1}']}]
            
            for obj in urls:

                if n + 1 > obj.get('limit'): continue

                await asyncio.sleep(random.uniform(1, 2.5)) 
                source = obj['source']
                for url in obj['urls']:
                    hrefs = None

                    if source == 'LogisQuebec':
                        text_data = await fetch_with_curl(url)

                    elif source == 'Louer':
                        hrefs = await self.browser.getPageHtml(url, source)
                        
                        if not hrefs:
                            return
                    
                    else:
                        response = await self.session.get(url)

                        if not response.ok:
                        
                            text_data = await fetch_with_curl(url)
                        
                        else:
                            
                            text_data = await response.text()

            
                
                    await self.save_links(text_data, source, hrefs)
                


    async def save_links(self, data, source, full_data=None):
        
        if not full_data:
            soup = BeautifulSoup(data, 'html.parser')
    
            anchors = soup.find_all('a')
            listings = [a.get('href') for a in anchors if a.get('href') and url_valid(a.get('href'), source)]

            if source == 'LogisQuebec':
            
                listings = ['https://www.logisquebec.com' + u for u in listings]
            
      
            if listings:
            
            
                await storelinks(listings, source)
        else:
            await storeFullData(full_data)
     
      

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
            for obj in links:
                l = obj[0]
                source = obj[3]

                await asyncio.sleep(random.uniform(2.5, 6.0))  ### Human like behavior
                valid = False
                data = await self.get_page(l)
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

                        


                if address:
                    if 'wendake' in address.lower() or 'g0a' in address.lower():
                        valid = True

                    elif description and 'wendake' in description.lower():
                        valid = True

                if price and int(price) > 950:
                        valid = False
                        

                if valid:
                        
                        self.notifier.send('Found an appartment !', f'Source: Kijiji, price: {price}$')
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                        print('\nFOUND A VALID APPARTMENT ON KIJIJI')
                        print(f'Price: {price}')
                        print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                await mark_valid({'url':l, 'price': price, 'valid': valid})
                        


    async def test_site(self):
        url=  'https://www.lespac.com/search/results?keywords=logement&geographicAreaId=15769&latitude=46.870284000000005&longitude=-71.36330700000018&cityLocation=true&categoryId=457'
 
         

        data = await self.browser.getPageHtml(url)
        print(data)
       
     
      


  

async def fetch_with_curl(url):
    process = await asyncio.create_subprocess_exec(
        "curl",
        "-4",  
        "-s",
        "-L",         
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print("curl error:", stderr.decode())
        return None
  
    return stdout.decode()






