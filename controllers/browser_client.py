from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import json
from playwright.async_api import async_playwright
import math
import logging 

class BrowserClient:
    def __init__(self):
        self.options = Options()
        self.logger = logging.getLogger(__name__)
        self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")

        self.playwright_client = None
        self.alt_driver = None
    
        
    def stop(self):
        if self.driver:
            self.driver.quit()
    
    def start(self):
        self.driver = webdriver.Chrome(options=self.options)

    async def start_alt(self):
        self.playwright_client = await async_playwright().start()
        self.alt_driver = await self.playwright_client.chromium.launch(headless=True, channel='chromium')
        self.page = await self.alt_driver.new_page()
     
    async def stop_alt(self):
        if self.alt_driver and self.playwright_client:
            await self.alt_driver.close()
            await self.playwright_client.stop()


    async def getPageHtml(self, url, source):

        
        if source in ['rentals', 'LesPacs']:
  
            await self.page.goto(url)

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
           
            self.driver.get(url)
            try:
                # Wait for at least one listing card to appear
                WebDriverWait(self.driver, 20).until(self.jsonld_ready)


                scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")

                listings = []

                for s in scripts:
                    try:
                        data = json.loads(s.get_attribute("innerHTML"))
                        if data.get("@type") in ["ApartmentComplex", "Apartment"]:
                            url = data.get('url', None)
                            if not url:
                                continue
                            price = data.get("potentialAction", {}).get("priceSpecification", {}).get("price") or None
                         
                            if price is None:
                                    listings = data.get('containsPlace', [])
                                    if listings:
                                        for i in listings:
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
                    except:
                        pass
               

                return {'result': listings, 'type': 'dataset'}
            
            except TimeoutException :
                self.logger.info(f'No more results : {url}')
                return None

      
        
        
    def jsonld_ready(self, driver):
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            for s in scripts:
                try:
                    txt = s.get_attribute("innerHTML")
                    if "Apartment" in txt or "ApartmentComplex" in txt:
                        return True
                except StaleElementReferenceException:
                    continue
            return False
        except:
            return False




    
