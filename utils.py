from dataclasses import dataclass
import csv
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse


@dataclass
class Product:
    title: str
    url: str
    price: Optional[float] = None
    deal_price: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None


def _parse_price(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    # remove common currency symbols and commas
    cleaned = re.sub(r"[^0-9\.\-]", "", value)
    try:
        return float(cleaned)
    except Exception:
        return None


def _is_valid_url(u: Optional[str]) -> bool:
    if not u:
        return False
    p = urlparse(u)
    return p.scheme in ("http", "https") and bool(p.netloc)


def read_products(csv_path: str) -> Tuple[List[Product], List[str]]:
    """Read and validate products from a CSV file.

    Returns a tuple (products, errors). Invalid rows are skipped but reported in errors.

    Expected column names (case-insensitive): title, url, price, deal_price, currency, image_url, tags
    The `tags` column may be a comma-separated list.
    """
    products: List[Product] = []
    errors: List[str] = []

    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=1):
            # normalize keys to lower-case
            data = {k.strip().lower(): (v or "").strip() for k, v in row.items()}

            title = data.get("title") or data.get("name")
            url = data.get("url") or data.get("link")

            if not title:
                errors.append(f"Row {i}: missing title")
                continue
            if not url or not _is_valid_url(url):
                errors.append(f"Row {i} ({title}): invalid or missing URL: {url}")
                continue

            price = _parse_price(data.get("price"))
            deal_price = _parse_price(data.get("deal_price") or data.get("sale_price"))
            currency = data.get("currency") or None
            image_url = data.get("image_url") or data.get("image") or None
            tags_raw = data.get("tags") or ""
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

            prod = Product(
                title=title,
                url=url,
                price=price,
                deal_price=deal_price,
                currency=currency,
                image_url=image_url,
                tags=tags,
            )
            products.append(prod)

    return products, errors


if __name__ == "__main__":
    import os
    csv_path = os.getenv("PRODUCTS_CSV", "products.csv")
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
    else:
        prods, errs = read_products(csv_path)
        print(f"Loaded {len(prods)} products")
        if errs:
            print("Errors:")
            for e in errs:
                print(" -", e)
