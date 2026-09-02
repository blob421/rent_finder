from bs4 import BeautifulSoup
import json
import re

logisqc_regex = r'^/[^/]+$'

sources = {'Kijiji': {"url": "https://www.kijiji.ca", "forbidden": 'radius='},
           'rentals': {"url": 'https://rentals.ca/quebec-city/'}}
#This function is for filtering <a> tags from a whole page 
def url_valid(url:str, source):
    if not url : return

    if source == 'Kijiji' and url.startswith("https://www.kijiji.ca") and not 'radius=' in url:
        return True
        
    elif source == 'rentals' and url.startswith('https://rentals.ca/quebec-city/'):
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
   
def parseLesPacs(html):
    soup = BeautifulSoup(html, 'html.parser')
    address = soup.find('div', id='detailProduct').get_text() or None
    price = soup.find('p', class_='price').get_text() or None
    description = soup.find('div', id='description').get_text() or None
  

    if price:
        price = clean_price(price)



    return address, price, description

### Function for extracting data from a products page in the form of ld+json scripts
def parse_json(data, source):
  
    if data.get('@type') and data['@type'] in ['SingleFamilyResidence', 'Product', 'RealEstateListing', 'Place',
                                               'LodgingBusiness', 'ApartmentComplex', 'Accommodation']:
        description = None
        address = None

        if source == 'RoomLala':
            description = data.get('description', None)
            location = data.get('address', {})
            address = location.get('postalCode', None)
            offers = data.get("makesOffer", [])
            price = None
            for offer in offers:
                spec = offer.get("priceSpecification", {})
                if spec.get("unitText") == "month":
                    price = spec.get("price", price)
             

        
        if source not in ['Louer', 'rentals', 'Rentola']:
         
            offers = data.get("offers") or {}
            price = offers.get("price", None)

        if source == 'Kijiji':

            address = data.get('address', None)
        

        elif source == 'LogisQuebec':
            location = data.get('address') or {}
            address = location.get('streetAddress', None)

 
        elif source == 'rentals':
            description = data.get('description', None)
            location = data.get('address', {})
            address = location.get('postalCode', None)
            price_items = data.get('containsPlace', None)
            if price_items is not None:
                price = None
                for i in price_items:
                    obj = i.get('potentialAction', {})
                    if not obj: continue

                    listing_price = obj.get('priceSpecification', {}).get('price', None)
                    if listing_price:
                          converted_price = int(listing_price)
                          if not price or converted_price < price:
                              price = converted_price


        elif source == 'DuProprio':
            address = data.get('name')
            description = data.get('description', None)
            
        elif source == 'GestiPro':
            location = data.get('address') or {}
            address = location.get('streetAddress', None) 
            description = data.get('description', None)
         

      
     
        new_data = {'address': address, 'price': price, 'description': description}
       
        return new_data
    
    return None


def hasStructureChanged(source, data):
    if not data.get('address') or len(data.get('address')) < 3:
        print(f'Address missing for {source}')

    if source in ['RoomLala', 'Louer', 'GestiPro', 'DuPropio']:

        if data.get('price') == None:
            print(f'Price not found for {source}')
            print('Stucture might have changed')

        if not data.get('description'):
            print(f'Description not found for {source}')
            print('Stucture might have changed')

    else:
        if data.get('price') == None:
            print(f'Price not found for {source}')
            print('Stucture might have changed')


import re

def clean_price(raw):
    if not raw:
        return None
       
    match = re.match(r'.?\d{1,3},\d{3}[.\s]*', raw)

    if not match:

        if (',' in raw and '.' in raw):
            raw = raw.split('.')[0]  ## $1,200.99 => 1,200

        elif ',' in raw:
            raw = raw.split(',')[0]  ## 1200,00   => 1200

        elif '.' in raw:
            raw = raw.split('.')[0]  ## 1200.99   => 1200

    cleaned = re.sub(r'[\sa-zA-Z,$]+', '', raw)  ## 1200

    try:
       return int(cleaned)
    except Exception:
        print(f'Wow this price is messed up ! :{raw}')

