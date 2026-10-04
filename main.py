from controllers.client import ClientMain
import asyncio
from aiohttp import ClientSession
from utils.db_calls import init_db
from controllers.notifications import Notifier
from controllers.browser_client import BrowserClient
from datetime import datetime
import json
import os
import re 
import random
import threading

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

buffer = []
def timeoutInput():
    buffer.append(input("\nUse this config ? (y or n) : "))

async def client_main(session, notifier, browser, config):
    
    print("\n\n######################################################")
    print("-------------------- RENT FINDER ---------------------")
    print("######################################################")
    print('\nReady to blast')
    client = ClientMain(session, notifier, browser, config)


    while True:
        
        start_time = datetime.now()

        #await client.test_site()
   
        #new_urls = await client.fetch_links()
        try:
          await client.process_links()
        except Exception as e:
            print(e)

        end_time = datetime.now()
        difference = (end_time - start_time).total_seconds() / 60
        print(f'\nMain loop finished at {end_time.strftime('%d/%m/%Y, %H:%M:%S')}')
        print(f'Duration : {difference} minutes')
       # print(f'New listings : {new_urls}\n') 
        
     
        await asyncio.sleep(60* 60 * 2 + random.uniform(5, 30))
      

async def main():
    await init_db()
    config = load_config()
  
    if not config:
        setup()

    notifier = Notifier()
    browser = BrowserClient()
    session = ClientSession()
    try:
        await client_main(session, notifier, browser, config)

    finally:
        await browser.stop_alt()
        
  
      
def load_config():

    if not os.path.exists(CONFIG_PATH):
        return None
    
    
    with open(CONFIG_PATH, 'r') as f:
        config = json.loads(f.read())
        keyword = config.get('keyword', None)
        price = config.get('max_price', None)
        postal = config.get('postal_code', None)
        min_price = config.get('min_price', None)

        if not keyword and not postal and not price :

            return None
          
        print('Config detected : ')
        print(f'Keyword: {keyword}, max_price: {price}, min_price:{min_price}, postal_code: {postal}')

        while True:
            buffer = []
            thread = threading.Thread(target=timeoutInput)
            thread.daemon = True
            thread.start()
            thread.join(20)
            
            if buffer:
                confirm = buffer[0]
                if confirm.lower().strip() in ('yes', 'y'):
                    return config
                
                elif confirm.lower().strip() in ('n', 'no'):
                    return None
                else:
                    print("Invalid choice , please enter (yes, no , y or n)")
                    continue
            else:
                return config
      
        
  

def setup():
    print("\n\n*********************** RENT FINDER SETUP ***********************\n")
    while True:
        keyword = input('Enter a keyword to look for in (description, address) : (enter to skip)')
     
        if keyword == '' or not keyword:
            break

        if not len(keyword) > 3:
            print('Invalid keyword, must be at lest 3 characters')
            continue

        confirm = input(f"Look for keyword '{keyword}' (y or n) : ")
        if confirm.lower().strip() == 'y' or confirm.lower().strip() == 'yes':
            keyword = keyword.strip().lower()
            break

        continue


    while True:
        max_price = input('\nEnter a maximum price (e.g. 950) : ')
        try:
            max_price = int(max_price)
            confirm = input(f"Confirm max_price of {max_price} (y or n) : ")
            if confirm.lower().strip() == 'y' or confirm.lower().strip() == 'yes':
                break
            continue
         
        except Exception:
            print('Invalid price , please provide a valid number')

    while True:
            min_price = input('\nEnter a minimum price (e.g. 750) : ')
            try:
                min_price = int(max_price)
                confirm = input(f"Confirm min_price of {min_price} (y or n) : ")
                if confirm.lower().strip() == 'y' or confirm.lower().strip() == 'yes':
                    break
                continue
            
            except Exception:
                print('Invalid price , please provide a valid number')

    while True:    

        postal_code = input('\nEnter a specific postal code or press ENTER to ignore : ')

        if postal_code == '' or not postal_code:
            break

        confirm = input(f"Confirm postal code '{postal_code}' (y or n) : ")
        if confirm.lower().strip() == 'y' or confirm.lower().strip() == 'yes':
            postal_code = re.sub(r'\s+', '', postal_code.lower())
            break


        continue

    p_alt = postal_code[0:(len(postal_code) // 2)] + " " + postal_code[(len(postal_code) // 2):]
 
    with open(CONFIG_PATH, 'w') as f:
        f.write(json.dumps({'keyword': keyword, 'max_price': max_price, 'min_price': min_price, 
                            'postal_code': postal_code , 'p_alt':p_alt}))
        
        print('Configuration saved in config.json')

asyncio.run(main())

