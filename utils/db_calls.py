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
async def storelinks(cur, data:list, source, err_str='Error storing links'):
   for url in data:
       
       await cur.execute("""INSERT OR IGNORE INTO links(url, source) VALUES(?, ?)""", [url, source])

@use_sqlite
async def get_links(cur, err_str='Failed to fetch links'):
    await cur.execute("""SELECT * FROM links WHERE checked=?""", [False])
    links = await cur.fetchall()
    if links:
        return [l for l in links] 
    
    return None

@use_sqlite
async def mark_valid(cur, obj, err_str='Err marking valid'):

    await cur.execute("""UPDATE links SET valid=?, price=?, checked=? WHERE url=?""", 
                                                  [obj['valid'], obj['price'], True, obj['url']])

@use_sqlite
async def storeFullData(cur, objs:list, err_str='Error storing full data'):
    for obj in objs:
        valid = False

        if 'g0a' in obj.get('address').lower():
            valid = True

        if obj.get('price') and int(obj.get('price')) > 950:
            valid = False
        
        await cur.execute("""INSERT OR IGNORE INTO links(url, valid, checked, price) VALUES(?,?,?,?)""", 
                                                  [obj.get('url') , valid, True, obj.get('price', None)])