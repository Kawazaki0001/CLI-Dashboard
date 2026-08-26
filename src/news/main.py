# news/main.py
import os, asyncio
from rich import console
from dotenv import load_dotenv
from httpx import AsyncClient

load_dotenv()

class News:
    """
    Fetch top 3 news articles from NewsAPI (everything endpoint).
    """
    def __init__(self):
        self.baseUrl = "https://newsapi.org/v2/everything"
        self.params = {
            "q": "finance",
            "pageSize": "3",
            "apiKey": os.getenv("News_Api_Key"),
        }
        self._news = []   # will hold the articles

    async def makeCall(self) -> list:
        """Fetch news and return list of articles."""
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.get(self.baseUrl, params=self.params)
                response.raise_for_status()
                data = response.json()
                self._news = data.get("articles", [])
                return self._news
        except Exception as e:
            print(f"News API error: {e}")
            return []   # fallback empty list

    def get_news(self) -> list:
        """Return the cached news list."""
        return self._news
