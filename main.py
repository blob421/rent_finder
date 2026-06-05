from controllers.client import ClientMain
import asyncio
from aiohttp import ClientSession
from utils.db_calls import init_db
from controllers.notifications import Notifier
from controllers.browser_client import BrowserClient
from datetime import datetime

async def client_main(session, notifier, browser):
    
    
    client = ClientMain(session, notifier, browser)

    while True:
        
        start_time = datetime.now()

        #await client.test_site()
        new_urls = await client.fetch_links()
        await client.process_links()

        end_time = datetime.now()
        difference = (end_time - start_time).total_seconds() / 60
        print(f'\nMain loop finished at {end_time.strftime('%d/%m/%Y, %H:%M:%S')}')
        print(f'Duration : {difference} minutes')
        print(f'New listings : {new_urls}\n')
        await asyncio.sleep(60* 60 * 2)
       

async def main():
    await init_db()
    notifier = Notifier()
    browser = BrowserClient()
    session = ClientSession()
    await asyncio.gather(client_main(session, notifier, browser))
      


asyncio.run(main())