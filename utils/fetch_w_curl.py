
import asyncio


async def fetch_with_curl(url):
    process = await asyncio.create_subprocess_exec(
        "curl",
        "-4",  
        "-s",
        "-L",
        "-w", "%{http_code}",         
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print("curl error:", stderr.decode())
        return None
    
    all = stdout.decode()
    body, code = all[:-3], all[-3:]

    result = {'result': None, 'type': 'error'} if code != '200' else {'result': body, 'type': 'page'}

    return result
