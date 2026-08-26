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

# <<< Design of Response format >>>

# [
#     {
#         'source': {'id': 'bbc-news', 'name': 'BBC News'},
#         'author': 'https://www.facebook.com/bbcnews',
#         'title': 'Ukraine hits two oil refineries deep in Russian territory',
#         'description': 'Ukraine\'s president says the strikes aim to limit revenues Russia "used to finance" its war.',
#         'url': 'https://www.bbc.co.uk/news/articles/cwymv212xrxo',
#         'urlToImage': 'https://ichef.bbci.co.uk/ace/branded_news/1200/cpsprodpb/4e4c/live/d37c5f10-9184-11f1-9587-294e25c71c14.png',
#         'publishedAt': '2026-08-06T12:18:48Z',
#         'content': 'Both Russia and Ukraine have in recent weeks intensified attacks on major cities, energy facilities and warehouses, as the vast front line remains virtually static and all mediation efforts to end
# th… [+1290 chars]'
#     },
#     {
#         'source': {'id': 'the-verge', 'name': 'The Verge'},
#         'author': 'Andrew J. Hawkins',
#         'title': 'Joby flexes military muscle with $500 million defense acquisition',
#         'description': 'Joby Aviation announced it was acquiring Dayton, Ohio-based defense firm Resonant Sciences in a $500 million deal, in a bid by the electric aircraft company to expand further into the military
# industrial complex. Joby says it expects to finance the deal with …',
#         'url': 'https://www.theverge.com/transportation/977533/joby-resonant-sciences-acquisition-evtol',
#         'urlToImage': 'https://platform.theverge.com/wp-content/uploads/sites/2/2026/06/DSC01507.jpg?quality=90&strip=all&crop=0%2C10.806933475316%2C100%2C78.386133049368&w=1200',
#         'publishedAt': '2026-08-11T12:03:16Z',
#         'content': '<ul><li></li><li></li><li></li></ul>\r\nThe eVTOL company is trying to shore up its defense business with the acquisition of the Dayton, Ohio-based firm.\r\nThe eVTOL company is trying to shore up
# its de… [+4248 chars]'
#     },
#     {
#         'source': {'id': None, 'name': 'Entrepreneur'},
#         'author': 'Sherin Shibu',
#         'title': 'ChatGPT Is Now Giving Out Personal Finance Advice. Here’s Where It Can Go Really Wrong.',
#         'description': 'Finance experts urge caution when it comes to seeking personal finance advice from AI.',
#         'url': 'https://www.entrepreneur.com/business-news/chatgpt-is-now-giving-out-personal-finance-advice-where-it-can-go-really-wrong',
#         'urlToImage': 'https://www.entrepreneur.com/wp-content/uploads/sites/2/2026/08/ChatGPT-GettyImages-2234202465.jpg?resize=1024,683',
#         'publishedAt': '2026-08-13T15:09:31Z',
#         'content': 'Key Takeaways\r\n<ul><li>Americans are increasingly using AI chatbots for everyday financial guidance.</li><li>In a recent JD Power financial health survey of 4,000 people, 40% said they had used AI
# to… [+3235 chars]'
#     }
# ]





