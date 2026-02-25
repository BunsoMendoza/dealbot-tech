from dotenv import load_dotenv
import os
import requests
from typing import Optional

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY")


def _template_tweet(title: str, url: str, deal_price: Optional[float], currency: Optional[str]) -> str:
    parts = []
    parts.append(title)
    if deal_price is not None:
        price_str = f"{currency or ''}{deal_price}".strip()
        parts.append(f"Now {price_str}!")
    parts.append(url)
    tweet = " — ".join(parts)
    if len(tweet) > MAX_POST_CHARS:
        max_title = MAX_POST_CHARS - (len(tweet) - len(title)) - 3
        title_short = title[: max(0, max_title)] + "..."
        parts[0] = title_short
        tweet = " — ".join(parts)
    return tweet


MAX_POST_CHARS = int(os.getenv("MAX_POST_CHARS", "500"))  # 500 for Threads, 280 for Twitter


def generate_tweet(product: object, style: Optional[str] = None) -> str:
    """Generate a short post for a product. Tries LLM provider when configured,
    otherwise falls back to a template.

    `product` is expected to have attributes: `title`, `url`, `deal_price`, `price`, `currency`, `tags`.
    """
    title = getattr(product, "title", "")
    url = getattr(product, "url", "")
    deal_price = getattr(product, "deal_price", None)
    price = getattr(product, "price", None)
    currency = getattr(product, "currency", None)

    # If provider is openai and key is present, call the API
    if LLM_PROVIDER == "openai" and LLM_API_KEY:
        try:
            system = (
                "You are a friendly, concise social media copywriter. Write a single Twitter post (<=280 chars)"
                " that highlights the product title, mentions the deal price if present, includes the product URL,"
                " and keeps the tone enthusiastic but factual. Do not invent discounts or false claims."
            )
            user = f"Product: {title}\nPrice: {price or 'N/A'}\nDeal price: {deal_price or 'N/A'}\nCurrency: {currency or ''}\nURL: {url}\n"
            if style:
                user += f"Style: {style}\n"

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 180,
            }

            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            }

            resp = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # Extract assistant content
            text = data.get("choices", [])[0].get("message", {}).get("content", "").strip()
            if text:
                # Ensure URL is included; simple safeguard
                if url and url not in text:
                    text = text.rstrip() + " " + url
                if len(text) > MAX_POST_CHARS:
                    text = text[:MAX_POST_CHARS - 3] + "..."
                return text
        except Exception:
            # fall through to template
            pass

    # Fallback template
    return _template_tweet(title=title, url=url, deal_price=deal_price or price, currency=currency)


if __name__ == "__main__":
    # simple smoke test
    class P:
        title = "Sample Product Name"
        url = "https://example.com/product"
        price = 49.99
        deal_price = 29.99
        currency = "$"

    print(generate_tweet(P()))
