
import asyncio


async def fetch_with_curl(url):
    process = await asyncio.create_subprocess_exec(
        "curl",
        "-4",  
        "-s",
        "-L",         
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print("curl error:", stderr.decode())
        return None
  
    return {'result': stdout.decode(), 'type': 'page'}
