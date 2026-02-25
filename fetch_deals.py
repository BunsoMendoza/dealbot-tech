"""fetch_deals.py — Pull tech deals from public RSS feeds into products.csv."""

import csv
import os
import re
import argparse
import feedparser

PRODUCTS_CSV = "products.csv"
FIELDNAMES = ["title", "url", "price", "deal_price", "currency", "image_url", "tags"]

# --- Feed configuration ---
# SlickDeals supports per-keyword RSS search. Set SLICKDEALS_KEYWORDS in your .env
# as a comma-separated list, e.g.: SLICKDEALS_KEYWORDS=laptop,gpu,monitor,headphones
# Leave unset to use the generic front-page feed.
SLICKDEALS_BASE = "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"

# DealNews category feeds. Set DEALNEWS_CATEGORIES in your .env (comma-separated).
# Available: electronics, computers, phones, tvs, gaming
# Default: electronics
DEALNEWS_FEEDS = {
    "electronics": "https://www.dealnews.com/c142/Electronics/?rss=1",
    "computers":   "https://www.dealnews.com/c143/Computers/?rss=1",
    "phones":      "https://www.dealnews.com/c131/Cell-Phones/?rss=1",
    "tvs":         "https://www.dealnews.com/c141/TVs/?rss=1",
    "gaming":      "https://www.dealnews.com/c154/Gaming/?rss=1",
}


def _build_feeds() -> list:
    feeds = []

    kw_env = os.getenv("SLICKDEALS_KEYWORDS", "").strip()
    if kw_env:
        for kw in kw_env.split(","):
            kw = kw.strip()
            if kw:
                feeds.append(f"{SLICKDEALS_BASE}&q={kw}")
    else:
        feeds.append(SLICKDEALS_BASE)

    cat_env = os.getenv("DEALNEWS_CATEGORIES", "electronics").strip()
    for cat in cat_env.split(","):
        cat = cat.strip().lower()
        if cat in DEALNEWS_FEEDS:
            feeds.append(DEALNEWS_FEEDS[cat])

    return feeds


# Keywords to keep (case-insensitive); empty list = keep everything
TECH_KEYWORDS = [
    "laptop", "monitor", "keyboard", "mouse", "headphone", "earbuds", "speaker",
    "tablet", "ipad", "phone", "ssd", "hard drive", "ram", "gpu", "cpu",
    "graphics card", "router", "switch", "hub", "usb", "cable", "charger",
    "power bank", "webcam", "microphone", "tv", "4k", "gaming", "console",
    "nintendo", "playstation", "xbox", "steam deck", "drone", "camera",
    "smartwatch", "apple", "samsung", "dell", "lenovo", "asus", "acer", "hp",
    "logitech", "razer", "corsair", "anker", "belkin", "intel", "amd", "nvidia",
]


def _parse_price_str(raw: str) -> float:
    return float(raw.replace(",", ""))


def _extract_price(text: str):
    """Return the first dollar price found in text, or None."""
    m = re.search(r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)", text)
    return _parse_price_str(m.group(1)) if m else None


def _extract_original_price(text: str):
    """Try to find an 'was $X' or 'reg $X' style original price."""
    m = re.search(r"(?:was|reg(?:ular)?|original|list|retail)[^\$]*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)", text, re.I)
    return _parse_price_str(m.group(1)) if m else None


def _extract_image(entry) -> str:
    for attr in ("media_thumbnail", "media_content"):
        val = getattr(entry, attr, None)
        if val and isinstance(val, list):
            return val[0].get("url", "")
    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href", "")
    return ""


def _is_tech(title: str, summary: str) -> bool:
    if not TECH_KEYWORDS:
        return True
    combined = (title + " " + summary).lower()
    return any(kw in combined for kw in TECH_KEYWORDS)


def load_existing_urls(path: str) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return {row.get("url", "") for row in reader}


def fetch_deals(feeds=None, limit=50, tags="tech") -> list:
    """Fetch entries from RSS feeds. Returns list of row dicts."""
    feeds = feeds or _build_feeds()
    rows = []
    seen_urls = set()

    for feed_url in feeds:
        print(f"Fetching: {feed_url}")
        parsed = feedparser.parse(feed_url)
        if parsed.bozo:
            print(f"  Warning: feed parse issue — {parsed.bozo_exception}")
        entries = parsed.entries[:limit]
        print(f"  Got {len(entries)} entries")

        for entry in entries:
            url = entry.get("link", "").strip()
            if not url or url in seen_urls:
                continue

            title = entry.get("title", "").strip()
            summary = entry.get("summary", "") or ""

            if not _is_tech(title, summary):
                continue

            # Price extraction: first price in title is usually deal price
            deal_price = _extract_price(title) or _extract_price(summary)
            original_price = _extract_original_price(title) or _extract_original_price(summary)

            rows.append({
                "title": title,
                "url": url,
                "price": original_price or "",
                "deal_price": deal_price or "",
                "currency": "$" if (deal_price or original_price) else "",
                "image_url": _extract_image(entry),
                "tags": tags,
            })
            seen_urls.add(url)

    return rows


def write_to_csv(rows: list, csv_path: str):
    existing_urls = load_existing_urls(csv_path)
    new_rows = [r for r in rows if r["url"] not in existing_urls]

    if not new_rows:
        print("No new deals to add.")
        return 0

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} new deals to {csv_path}")
    return len(new_rows)


def main():
    parser = argparse.ArgumentParser(description="Fetch tech deals into products.csv")
    parser.add_argument("--csv", default=os.getenv("PRODUCTS_CSV", PRODUCTS_CSV))
    parser.add_argument("--limit", type=int, default=50, help="Max entries per feed")
    parser.add_argument("--tags", default="tech", help="Tag string to apply to all rows")
    parser.add_argument("--dry-run", action="store_true", help="Print deals without writing CSV")
    args = parser.parse_args()

    rows = fetch_deals(limit=args.limit, tags=args.tags)
    print(f"\nTotal tech deals found: {len(rows)}")

    if args.dry_run:
        for r in rows:
            price_info = f"  deal=${r['deal_price']} orig=${r['price']}" if r["deal_price"] else ""
            print(f"  {r['title'][:80]}{price_info}")
            print(f"    {r['url']}")
    else:
        write_to_csv(rows, args.csv)


if __name__ == "__main__":
    main()
