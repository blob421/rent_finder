from controllers.client import ClientMain
import asyncio
from aiohttp import ClientSession
from utils.db_calls import init_db
from controllers.notifications import Notifier
from controllers.browser_client import BrowserClient

async def client_main(session, notifier, browser):
    
    
    client = ClientMain(session, notifier, browser)

    while True:
        #await client.test_site()
        #await client.fetch_links()
        await client.filterLinks()
        await asyncio.sleep(60* 60 * 2)

async def main():
    await init_db()
    notifier = Notifier()
    browser = BrowserClient()
    session = ClientSession()
    await asyncio.gather(client_main(session, notifier, browser))
      


asyncio.run(main())