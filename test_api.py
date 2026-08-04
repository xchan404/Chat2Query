import asyncio
import httpx
from app.config import get_settings

async def test():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post('https://api.anthropic.com/v1/messages', 
                                    headers={'x-api-key': get_settings().ANTHROPIC_API_KEY, 
                                             'anthropic-version': '2023-06-01', 
                                             'content-type': 'application/json'}, 
                                    json={'model': 'claude-3-5-haiku-20241022', 
                                          'max_tokens': 1024, 
                                          'messages': [{'role': 'user', 'content': 'test'}]})
            print("STATUS CODE:", res.status_code)
            print("RESPONSE TEXT:", res.text)
    except Exception as e:
        print("EXCEPTION:", e)

asyncio.run(test())
