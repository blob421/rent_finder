from controllers.kijiji import Kijiji
import asyncio
from aiohttp import ClientSession
from utils.db_calls import init_db
from controllers.notifications import Notifier


async def kijiji_main(session, notifier):
    

    kijiji = Kijiji(session, notifier)

    while True:
       
        await kijiji.fetch_links()
        await kijiji.filterLinks()
        await asyncio.sleep(60* 60)

async def main():
    await init_db()
    notifier = Notifier()
    session = ClientSession()
    await asyncio.gather(kijiji_main(session, notifier))
      


asyncio.run(main())