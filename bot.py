import time
import json
import os
import argparse
import logging
from datetime import datetime, timezone
from typing import List

from utils import read_products, Product
from llm import generate_tweet
from twitter_client import TwitterClient
from threads_client import ThreadsClient
from fetch_deals import fetch_deals, write_to_csv

logger = logging.getLogger(__name__)


POSTED_DB = "posted.json"
LAST_RUN_FILE = "last_run.txt"


class Bot:
	def __init__(self, products_csv: str, twitter_client: TwitterClient):
		self.products_csv = products_csv
		self.client = twitter_client
		self.posted = self._load_posted()

	def _load_posted(self):
		if os.path.exists(POSTED_DB):
			try:
				with open(POSTED_DB, "r", encoding="utf-8") as fh:
					return json.load(fh)
			except Exception:
				return {}
		return {}

	def _save_posted(self):
		with open(POSTED_DB, "w", encoding="utf-8") as fh:
			json.dump(self.posted, fh, indent=2)

	def select_products(self) -> List[Product]:
		prods, errs = read_products(self.products_csv)
		# simple: skip any product whose url was posted before
		filtered = [p for p in prods if p.url not in self.posted]
		return filtered

	def post_product(self, product: Product) -> bool:
		tweet = generate_tweet(product)
		try:
			resp = self.client.post_tweet(tweet)
			# record posted time
			self.posted[product.url] = {
				"title": product.title,
				"tweet_id": resp.get("id") if isinstance(resp, dict) else None,
				"posted_at": datetime.now(timezone.utc).isoformat(),
			}
			self._save_posted()
			# update last run marker
			try:
				with open(LAST_RUN_FILE, "w", encoding="utf-8") as fh:
					fh.write(datetime.now(timezone.utc).isoformat())
			except Exception:
				logger.exception("Failed to write last run file")
			return True
		except Exception as e:
			print(f"Failed to post {product.url}: {e}")
			return False

	def _refresh_deals(self):
		rows = fetch_deals()
		added = write_to_csv(rows, self.products_csv)
		if added:
			logger.info("Fetched %d new deals into %s", added, self.products_csv)

	def run_once(self, limit: int = 1):
		self._refresh_deals()
		products = self.select_products()
		posted = 0
		for p in products:
			if posted >= limit:
				break
			ok = self.post_product(p)
			if ok:
				posted += 1

	def run_loop(self, interval_minutes: int = 60, per_run: int = 1):
		logger.info("Starting loop: every %d minutes, %d posts per run", interval_minutes, per_run)
		try:
			while True:
				self.run_once(limit=per_run)
				time.sleep(interval_minutes * 60)
		except KeyboardInterrupt:
			logger.info("Stopping loop")


def main():
	parser = argparse.ArgumentParser(description="DealBot scheduler")
	parser.add_argument("--csv", default=os.getenv("PRODUCTS_CSV", "products.csv"))
	parser.add_argument("--once", action="store_true", help="Run a single posting run and exit")
	parser.add_argument("--limit", type=int, default=1, help="Number of posts per run")
	parser.add_argument("--interval", type=int, default=60, help="Minutes between runs when running continuously")
	args = parser.parse_args()

	logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

	platform = os.getenv("PLATFORM", "threads").lower()
	if platform == "twitter":
		client = TwitterClient()
	else:
		client = ThreadsClient()
	bot = Bot(args.csv, client)

	if args.once:
		bot.run_once(limit=args.limit)
	else:
		bot.run_loop(interval_minutes=args.interval, per_run=args.limit)


if __name__ == "__main__":
	main()

