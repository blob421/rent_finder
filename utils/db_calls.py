import aiosqlite
import os
from datetime import datetime 

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
    await cur.execute("""CREATE TABLE IF NOT EXISTS links(date TEXT,
                                                        url TEXT UNIQUE,
                                                        checked BOOLEAN DEFAULT false, 
                                                        valid BOOLEAN DEFAULT false,
                                                        source VARCHAR(50),
                                                        price INTEGER DEFAULT NULL)""")
    
    await cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS "unique_url_prefix" ON "links" ("url_prefix")""")
    

@use_sqlite
async def storelinks(cur, data:list, source, err_str='Error storing links'):
    time = datetime.now().isoformat()
    inserted = 0
    if source == 'LesPacs':
        for url in data:
            prefix = url.split('.jsa')[0] if '.jsa' in url else url
            await cur.execute("""INSERT OR IGNORE INTO links(date, url, source, url_prefix) VALUES(?, ?, ?, ?)""", 
                              [time, url, source, prefix])
            inserted += cur.rowcount
    else:

        for url in data:
            
            await cur.execute("""INSERT OR IGNORE INTO links(date, url, source) VALUES(?, ?, ?)""", [time, url, source])
            inserted += cur.rowcount
    return inserted

   

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
async def storeFullData(cur, obj:object, source, err_str='Error storing full data'):
    time = datetime.now().isoformat()
   

    await cur.execute("""INSERT OR IGNORE INTO links(date, url, valid, source, checked, price) VALUES(?,?,?,?,?,?)""", 
                                                  [time, obj.get('url') , obj.get('valid'), source, True, obj.get('price', None)])
    
    return cur.rowcount