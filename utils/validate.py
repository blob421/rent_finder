def url_valid(url:str, source):
    if not url : return
    if url.startswith("https://www.kijiji.ca") and not 'radius=' in url:
        return True
    elif source == 'LogisQuebec' and url.startswith('/') and len(url) > 10:
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
    

def parse_json(data, source):
    
    if data.get('@type') and data['@type'] in ['SingleFamilyResidence', 'Product', 'RealEstateListing', 'Place']:
        description = None
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

        elif source == 'Louer':
            actions = data.get('potentialAction') or {}
            specs = actions.get('priceSpecification', {})
            price = specs.get('price', None)
            description = data.get('description', None)

            location = data.get('address') or {}
            address = location.get('postalCode', None)



        return {'address': address, 'price': price, 'description': description}
    
    return None


