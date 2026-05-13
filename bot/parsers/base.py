import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    def __init__(self, shop_name: str, base_url: str):
        self.shop_name = shop_name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str) -> Optional[str]:
        if not self.session:
            self.session = aiohttp.ClientSession()

        for attempt in range(3):
            try:
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    logger.warning(f"Attempt {attempt + 1} failed: {response.status}")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")

        return None

    @abstractmethod
    async def parse_price(self, html: str) -> Optional[float]:
        pass

    @abstractmethod
    async def parse_availability(self, html: str) -> bool:
        pass

    async def get_product_info(self, url: str) -> dict:
        html = await self.fetch(url)
        if not html:
            return {"price": None, "available": False, "error": "Failed to fetch"}

        return {
            "price": await self.parse_price(html),
            "available": await self.parse_availability(html),
            "raw_html": html[:500]
        }


class AvitoParser(BaseParser):
    def __init__(self):
        super().__init__("Avito", "https://www.avito.ru")

    async def parse_price(self, html: str) -> Optional[float]:
        soup = BeautifulSoup(html, "lxml")
        price_element = soup.select_one("[data-item-id] [class*='price']")
        if price_element:
            text = price_element.get_text()
            digits = "".join(filter(str.isdigit, text.split()[0] if text else ""))
            return float(digits) if digits else None
        return None

    async def parse_availability(self, html: str) -> bool:
        soup = BeautifulSoup(html, "lxml")
        unavailable = soup.select_one("[class*='item-unavailable']")
        return unavailable is None


class OllxParser(BaseParser):
    def __init__(self):
        super().__init__("OLX", "https://www.olx.ru")

    async def parse_price(self, html: str) -> Optional[float]:
        soup = BeautifulSoup(html, "lxml")
        price_element = soup.select_one("[class*='price']")
        if price_element:
            text = price_element.get_text()
            digits = "".join(filter(str.isdigit, text.split()[0] if text else ""))
            return float(digits) if digits else None
        return None

    async def parse_availability(self, html: str) -> bool:
        soup = BeautifulSoup(html, "lxml")
        return "нет в наличии" not in html.lower()


class FishingShopParser(BaseParser):
    def __init__(self, shop_name: str, base_url: str, price_selector: str = "[class*='price']"):
        super().__init__(shop_name, base_url)
        self.price_selector = price_selector

    async def parse_price(self, html: str) -> Optional[float]:
        soup = BeautifulSoup(html, "lxml")
        price_element = soup.select_one(self.price_selector)
        if price_element:
            text = price_element.get_text()
            digits = "".join(filter(str.isdigit, text.split()[0] if text else ""))
            return float(digits) if digits else None
        return None

    async def parse_availability(self, html: str) -> bool:
        return "нет в наличии" not in html.lower() and "out of stock" not in html.lower()


PARSERS = {
    "avito": AvitoParser,
    "olx": OllxParser,
}


async def parse_product(parser_name: str, url: str) -> dict:
    if parser_name in PARSERS:
        parser_class = PARSERS[parser_name]
    else:
        parser_class = FishingShopParser

    async with parser_class() as parser:
        return await parser.get_product_info(url)


async def parse_multiple_sources(urls: list) -> list:
    tasks = []
    for url in urls:
        if "avito" in url:
            tasks.append(parse_product("avito", url))
        elif "olx" in url:
            tasks.append(parse_product("olx", url))
        else:
            tasks.append(parse_product("generic", url))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]