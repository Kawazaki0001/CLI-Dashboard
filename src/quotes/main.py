""" We get the free quotes from https://zenquotes.io and return it first text then author """
import asyncio
from httpx import AsyncClient


async def getQuote() :
    async with AsyncClient() as client :
        res = await client.get(url="https://zenquotes.io/api/random")
        res.raise_for_status()
        obj = res.json()[0]
        return (obj.get('q'), obj.get('a'))
