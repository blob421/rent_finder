from bs4 import BeautifulSoup

import aiohttp
import json
import asyncio
from utils.db_calls import storelinks, get_links, mark_valid
import random


class Kijiji:
    def __init__(self, client):
        self.session = client
   
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
    async def fetch_links(self, err_str='Error fetching kijiji links'):
        for n in range(4):
            await asyncio.sleep(random.uniform(2, 3))
            url = f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/logement/page-{n+1}/k0c30349001l1700121?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list'
            response = await self.session.get(url)
            text_data = await response.text()
        
            await self.save_links(text_data)
                
            
        for n in range(4):
            await asyncio.sleep(random.uniform(2, 3))
            url = f'https://www.kijiji.ca/b-a-louer/ville-de-quebec/chambre/page-{n+1}/k0c30349001l1700124?ll=46.8715568%2C-71.36205240000001&radius=4.0&view=list'
            response = await self.session.get(url)
            text_data = await response.text()
            await self.save_links(text_data)


    async def save_links(self, data):
        soup = BeautifulSoup(data, 'html.parser')

        anchors = soup('a')
        listings = [a.get('href') for a in anchors if a.get('href') and a.get('href').startswith("https://www.kijiji.ca") and not 'radius=' in a.get('href')]
        if listings:
          
           
            await storelinks(listings)
     
      

#################### RETRIEVING AND FILTERING #######################################################


    @use_session
    async def get_page(self, url, err_str='Failed to get a single page'):
        response=  await self.session.get(url) 
        text_data = await response.text()
        return text_data

    
    async def filterLinks(self):
        links = await get_links()       ### ALL links that are not checked 
      
        if links:
            for l in links:
                await asyncio.sleep(random.uniform(2.5, 6.0))  ### Human like behavior
                valid = False
                data = await self.get_page(l)
                soup = BeautifulSoup(data, 'html.parser')
                scripts = soup.find_all("script", {"type": "application/ld+json"}) 


                for s in scripts:
                    data = s.string
                    parsed = json.loads(data)
                    if parsed['@type'] == 'SingleFamilyResidence':

                        offers = parsed.get("offers") or {}
                        price = offers.get("price")

                        address = parsed.get('address') or ""
                        if address:
                            if 'wendake' in address.lower() or 'g0a' in address.lower():
                                valid = True

                        if price and int(price) > 950:
                                valid = False

                        if valid:
                            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                            print('\nFOUND A VALID APPARTMENT ON KIJIJI')
                            print(f'Price: {price}')
                            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                        await mark_valid({'url':l, 'price': price, 'valid': valid})
                        













