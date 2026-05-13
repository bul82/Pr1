import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ShopVerifier:
    CHECK_WEIGHTS = {
        "domain_age": 0.2,
        "has_contact_info": 0.15,
        "https": 0.1,
        "price_aligned": 0.25,
        "reviews_exist": 0.2,
        "ssl_valid": 0.1,
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_domain_age(self, url: str) -> int:
        parsed = urlparse(url)
        domain = parsed.netloc
        logger.info(f"Checking domain age for: {domain}")
        await asyncio.sleep(0.1)
        return 365

    async def check_contact_info(self, url: str) -> bool:
        html = await self._fetch_url(url)
        if not html:
            return False

        contact_indicators = ["контакт", "телефон", "email", "адрес", "contact", "phone"]
        return any(ind in html.lower() for ind in contact_indicators)

    async def check_https(self, url: str) -> bool:
        return url.startswith("https://")

    async def check_ssl(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc
            async with self.session.get(url, ssl=True, timeout=5) as resp:
                return resp.status == 200
        except:
            return False

    async def check_price_aligned(self, url: str, market_avg_price: float = 3000) -> float:
        from bot.parsers.base import parse_product
        result = await parse_product("generic", url)
        price = result.get("price")

        if not price:
            return 0.0

        diff_percent = abs(price - market_avg_price) / market_avg_price

        if diff_percent < 0.3:
            return 1.0
        elif diff_percent < 0.5:
            return 0.5
        elif diff_percent < 0.7:
            return 0.2
        else:
            return 0.0

    async def check_reviews(self, url: str) -> tuple[bool, int]:
        html = await self._fetch_url(url)
        if not html:
            return False, 0

        review_indicators = ["отзыв", "review", "рейтинг", "rating"]
        has_reviews = any(ind in html.lower() for ind in review_indicators)

        review_count = 0
        if has_reviews:
            for word in ["100", "200", "500", "1000"]:
                if word in html:
                    review_count = int(word)
                    break

        return has_reviews, review_count

    async def verify_shop(self, url: str, market_avg_price: float = 3000) -> Dict:
        checks = {
            "domain_age": await self.check_domain_age(url),
            "has_contact_info": await self.check_contact_info(url),
            "https": await self.check_https(url),
            "price_aligned": await self.check_price_aligned(url, market_avg_price),
            "reviews_exist": await self.check_reviews(url),
            "ssl_valid": await self.check_ssl(url),
        }

        rating = sum(
            self.CHECK_WEIGHTS[k] * (v / 100 if k == "domain_age" else float(v))
            for k, v in checks.items()
            if k != "reviews_exist"
        )

        has_reviews, review_count = checks["reviews_exist"]
        if has_reviews:
            review_score = min(review_count / 100, 1.0) * self.CHECK_WEIGHTS["reviews_exist"]
            rating += review_score

        verified = rating >= 0.7

        return {
            "rating": round(rating, 2),
            "verified": 1 if verified else 0,
            "domain_age_days": checks["domain_age"],
            "has_contact_info": 1 if checks["has_contact_info"] else 0,
            "review_count": review_count,
            "checks_detail": checks,
        }

    async def _fetch_url(self, url: str) -> Optional[str]:
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return None


async def verify_shop(shop_url: str, market_avg_price: float = 3000) -> Dict:
    async with ShopVerifier() as verifier:
        return await verifier.verify_shop(shop_url, market_avg_price)


async def verify_multiple_shops(shops: list) -> list:
    tasks = [verify_shop(shop["url"], shop.get("avg_price", 3000)) for shop in shops]
    return await asyncio.gather(*tasks)


AUTHENTICITY_CHECKLIST = {
    "serial_number": "Проверьте серийный номер на сайте производителя",
    "logo_quality": "Сравните качество логотипа с официальным",
    "packaging": "Проверьте упаковку на наличие голографических наклеек",
    "price_too_low": "Слишком низкая цена — признак подделки",
    "seller_location": "Проверьте место отправки продавца",
}


def check_authenticity(gear_name: str, price: float, seller_url: str) -> Dict:
    issues = []
    recommendations = []

    if price < 1000:
        issues.append("Цена подозрительно низкая")

    recommendations.append(AUTHENTICITY_CHECKLIST["serial_number"])
    recommendations.append(AUTHENTICITY_CHECKLIST["price_too_low"])

    return {
        "is_suspicious": len(issues) > 0,
        "issues": issues,
        "checklist": recommendations,
    }


def format_verification_report(shop_data: Dict) -> str:
    rating = shop_data.get("rating", 0)
    status = "✅ Проверен" if shop_data.get("verified") else "⚠️ Не проверен"

    report = f"""
🏪 Магазин: {shop_data.get("name", "Неизвестен")}
{status}

📊 Общий рейтинг: {rating}/1.0

Проверки:
"""

    checks = shop_data.get("checks_detail", {})
    for check_name, value in checks.items():
        if check_name == "domain_age":
            status_icon = "✅" if value > 180 else "⚠️"
            report += f"  {status_icon} Возраст домена: {value} дней\n"
        elif check_name == "has_contact_info":
            status_icon = "✅" if value else "⚠️"
            report += f"  {status_icon} Контактная информация: {'Есть' if value else 'Нет'}\n"
        elif check_name == "https":
            status_icon = "✅" if value else "❌"
            report += f"  {status_icon} HTTPS: {'Да' if value else 'Нет'}\n"
        elif check_name == "price_aligned":
            status_icon = "✅" if value > 0.5 else "⚠️"
            report += f"  {status_icon} Цены соответствуют рынку: {value*100:.0f}%\n"

    return report