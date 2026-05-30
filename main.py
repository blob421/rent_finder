from controllers.kijiji import Kijiji
import asyncio
from aiohttp import ClientSession
from utils.db_calls import init_db

async def kijiji_main(session):
    kijiji = Kijiji(session)
    while True:
       
        await kijiji.fetch_links()
        await kijiji.filterLinks()
        await asyncio.sleep(60* 60)

async def main():
    await init_db()
    session = ClientSession()
    await asyncio.gather(kijiji_main(session))
      


asyncio.run(main())