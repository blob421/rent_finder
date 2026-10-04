import json
from playwright.async_api import async_playwright
import math
import logging 
from bs4 import BeautifulSoup

class BrowserClient:
    def __init__(self):
   
        self.logger = logging.getLogger(__name__)
        self.playwright_client = None
        self.alt_driver = None
        self.page = None

    async def start_alt(self):
        self.playwright_client = await async_playwright().start()
        #self.alt_driver = await self.playwright_client.chromium.launch(headless=True, channel='chromium')
        self.alt_driver = await self.playwright_client.chromium.launch(headless=False)
        self.page = await self.alt_driver.new_page()
     
    async def stop_alt(self):
        if self.page:
              await self.page.close()
              
        if self.alt_driver and self.playwright_client:      
            await self.alt_driver.close()
            await self.playwright_client.stop()


    async def getPageHtml(self, url, source):

        
        if source in ['rentals', 'LesPacs']:
  
            resp = await self.page.goto(url)
          
            if not resp.ok:
                return {'result': None, 'type': 'error'}

            if source == 'LesPacs':

                for i in range(4):
                    portion = math.floor(5 - i)
                

                    await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight / {portion})")
                    await self.page.wait_for_timeout(500)

                for i in range(3):
                    portion = 1 + ((4 - i) * 0.20)
                    await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight / {portion})")
                    await self.page.wait_for_timeout(500)

                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(500)

            html = await self.page.content()

            return {'result': html, 'type': 'page'}
        
       
            
        elif source == 'Louer':
                listings = []
                known_urls = set()

                resp = await self.page.goto(url)
                if not resp.ok:
                    return {'result': None, 'type': 'error'}
    
                for i in range(6):
                        portion = math.floor(5 - i)

                        await self.page.evaluate("""
                                async () => {
                                    const el = document.querySelector('.r-listings-list');
                                    if (!el) return;
                               
                                    el.scrollBy(0, 600);
                            
                                }
                            """)
                        await self.page.wait_for_timeout(500)
                
            
                        html = await self.page.content()
                        list, known = await self.scroll_louer(html, known_urls, listings)
                        known_urls = known_urls.union(known)
                        listings.extend(list)

        return {'result': listings, 'type': 'dataset'}

                     
        
    async def scroll_louer(self, html, known, list):

        listings = []
        known_urls = set()

        soup = BeautifulSoup(html , 'html.parser')
        scripts = soup.find_all('script', {"type": "application/ld+json"})
    
        for s in scripts:

            try:
                data = json.loads(s.get_text())
                if data.get("@type") in ["ApartmentComplex", "Apartment", "Room"]:
                    url = data.get('url', None)

                    if not url:
                        continue
                    if url in known:
                        continue

                    known_urls.add(url)


                    price = data.get("potentialAction", {}).get("priceSpecification", {}).get("price") or None
                    
                    if price is None:
                            contain = data.get('containsPlace', [])
                            if contain:
                                for i in contain:
                                    pot = i.get('potentialAction', {})
                                    spec = pot.get('priceSpecification', {})
                                    listing_price = spec.get('price')

                                    if listing_price is not None:
                                        # Convert both to int safely
                                        try:
                                            lp = int(listing_price)
                                        except:
                                            continue

                                        if price is None or lp < int(price):
                                            price = lp

                    listings.append({
                        "url": data.get("url"),
                        "price": price,
                        "address": data.get("address", {}).get('postalCode', None),
                    
                    })

        

            except Exception: 
                pass

        return listings, known_urls




    
