from bs4 import BeautifulSoup
import json
import re

logisqc_regex = r'^/[^/]+$'

#This function is for filtering <a> tags from a whole page 
def url_valid(url:str, source):
    if not url : return
    if url.startswith("https://www.kijiji.ca") and not 'radius=' in url:
        return True
    elif source == 'LogisQuebec' and url.startswith('/') and len(url) > 20 and re.match(logisqc_regex, url):
        return True
    elif source == 'LesPacs' and url.startswith('https://www.lespac.com/'):
        return True
    elif source == 'DuProprio' and url.startswith('https://duproprio.com/fr/location/quebec-rive-nord/'):
        return True
    elif source == 'GestiPro' and url.startswith('https://gestipro.info/propriete/'):
        return True
    elif source == 'Centris' and url.startswith('https://www.centris.ca/fr/'):
        return True
    
    elif source == 'Louer' and url.startswith('/quebec-city/'):
        return True
    else:
        return False
    

### Function for extrating data from a list of cards in the form of ld+json scripts.  
def extractRootJson(data, source):
    soup = BeautifulSoup(data, 'html.parser')
    scripts = soup.find_all("script", {"type": "application/ld+json"}) 
    urls = []
    if scripts:
        for s in scripts:
            text = s.string
            parsed = json.loads(text)
          
            if source == 'RoomLala':
                if parsed.get('@type') == 'ItemList':
                    item_list = parsed.get('itemListElement', [])
                    if item_list:
                        for i in item_list:
                            item = i.get('item', {})
                            url:str = item.get('url', None)
                            if not url: continue
                            urls.append('https://fr.roomlala.ca' + url.replace('\\', '/'))

        return urls
   
    
### Function for extracting data from a products page in the form of ld+json scripts
def parse_json(data, source):
  
    if data.get('@type') and data['@type'] in ['SingleFamilyResidence', 'Product', 'RealEstateListing', 'Place',
                                               'LodgingBusiness', 'ApartmentComplex']:
        description = None
        address = None

        if source == 'RoomLala':
            description = data.get('description', None)
            location = data.get('address', {})
            address = location.get('postalCode', None)
            offers = data.get("makesOffer", [])
            print(address)
            price = None
            for offer in offers:
                spec = offer.get("priceSpecification", {})
                if spec.get("unitText") == "month":
                    price = spec.get("price", price)
                    print(price)


        if source != 'Louer':
         
            offers = data.get("offers") or {}
            price = offers.get("price", None)

        if source == 'Kijiji':

            address = data.get('address', None)
        
        elif source == 'LogisQuebec':
            location = data.get('address') or {}
            address = location.get('streetAddress', None)
        

        elif source == 'DuProprio':
            address = data.get('name')
            description = data.get('description', None)
            
        elif source == 'GestiPro':
            location = data.get('address') or {}
            address = location.get('streetAddress', None) 
            description = data.get('description', None)
            print(description)

      
      
        new_data = {'address': address, 'price': price, 'description': description}
       
        return new_data
    
    return None


def hasStructureChanged(source, data):
    if source in ['RoomLala', 'Louer', 'GestiPro', 'DuPropio']:

        if not data.get('price'):
            print(f'Price not found for {source}')
            print('Stucture might have changed')

        if not data.get('description'):
            print(f'Description not found for {source}')
            print('Stucture might have changed')

    else:
        if not data.get('price'):
            print(f'Price not found for {source}')
            print('Stucture might have changed')

