from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import json


class BrowserClient:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=self.options)

    def done(self):
        self.driver.quit()

    def start(self):
        self.driver = webdriver.Chrome(options=self.options)

    async def getPageHtml(self, url, source):

        self.driver.get(url)

        if source == 'Louer':
            try:
                # Wait for at least one listing card to appear
                WebDriverWait(self.driver, 20).until(
                    lambda d: any(
                        (
                            "Apartment" in (txt := s.get_attribute("innerHTML")) or
                            "ApartmentComplex" in txt
                        ) and '"url"' in txt
                        for s in d.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
                    )
                )


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
               

                return listings
            
            except TimeoutException :
                print(f'No results : {url}\n Error: No more results')
                return None

            
        
        

        else: 

            cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-listing-regionid]")

            results = []

            for card in cards:
                try:
                
                    link = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    print(link)
                except:
                    link = None

                price = card.get_attribute("data-listing-price")
                listing_id = card.get_attribute("data-listing-id")
                region = card.get_attribute("data-listing-region")
                address = card.find_element(By.CSS_SELECTOR, "[data-cy*='cellDistanceList']").text

                results.append({
                    "id": listing_id,
                    "url": link,
                    "price": price,
                    "address": address,
                    "region": region
                })

            return results


    
