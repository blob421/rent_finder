import aiosqlite
import os

current_dir = os.path.dirname(__file__)
db_path = os.path.abspath(os.path.join(current_dir, '../', 'db.sqlite'))

def use_sqlite(fn):
    async def wrapper(*args, **kwargs):
        try:
            async with aiosqlite.connect(db_path) as conn:
                async with conn.cursor() as cur:
                    result = await fn(cur, *args, **kwargs)
                    await conn.commit()
                    return result


        except aiosqlite.Error as e:
            print(f'{kwargs.get("err_str")}: {e}')

    return wrapper
        

@use_sqlite
async def init_db(cur, err_str="Failed to init db"):
    await cur.execute("""CREATE TABLE IF NOT EXISTS links(url TEXT UNIQUE,
                                                        checked BOOLEAN DEFAULT false, 
                                                        valid BOOLEAN DEFAULT false,
                                                        source VARCHAR(50),
                                                        price INTEGER DEFAULT NULL)""")
    

@use_sqlite
async def storelinks(cur, data:list, err_str='Error storing links'):
   for url in data:
       
       await cur.execute("""INSERT OR IGNORE INTO links(url) VALUES(?)""", [url])

@use_sqlite
async def get_links(cur, err_str='Failed to fetch links'):
    await cur.execute("""SELECT * FROM links WHERE checked=?""", [False])
    links = await cur.fetchall()
    if links:
        return [l[0] for l in links] 
    
    return None

@use_sqlite
async def mark_valid(cur, obj, err_str='Err marking valid'):

    await cur.execute("""UPDATE links SET valid=?, price=?, checked=? WHERE url=?""", 
                                                  [obj['valid'], obj['price'], True, obj['url']])

