"""threads_client.py — Post to Meta Threads via the Threads API v1.0."""

from dotenv import load_dotenv
import os
import time
import logging
import requests
from typing import Dict, Optional

load_dotenv()

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"


class ThreadsClient:
    """Post to Threads using the Threads API (two-step: create container → publish).

    Requires in .env:
      THREADS_USER_ID       — your numeric Threads user ID
      THREADS_ACCESS_TOKEN  — long-lived access token (valid ~60 days)
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.user_id = user_id or os.getenv("THREADS_USER_ID")
        self.access_token = access_token or os.getenv("THREADS_ACCESS_TOKEN")

        missing = [
            name
            for name, val in (
                ("THREADS_USER_ID", self.user_id),
                ("THREADS_ACCESS_TOKEN", self.access_token),
            )
            if not val
        ]
        if missing:
            raise EnvironmentError(f"Missing Threads credentials: {', '.join(missing)}")

    def _create_container(self, text: str) -> str:
        """Step 1: Create a text media container. Returns the creation_id."""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads"
        params = {
            "media_type": "TEXT",
            "text": text,
            "access_token": self.access_token,
        }
        resp = requests.post(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        creation_id = data.get("id")
        if not creation_id:
            raise ValueError(f"No creation_id in response: {data}")
        return creation_id

    def _publish_container(self, creation_id: str) -> Dict:
        """Step 2: Publish the container. Returns the API response."""
        url = f"{THREADS_API_BASE}/{self.user_id}/threads_publish"
        params = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }
        resp = requests.post(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def post_tweet(self, text: str) -> Dict:
        """Create and publish a Threads post. Returns the API response.

        Named post_tweet for interface compatibility with TwitterClient.
        """
        attempts = 3
        backoff = 2
        last_err = None

        for attempt in range(1, attempts + 1):
            try:
                creation_id = self._create_container(text)
                # Brief pause — Meta recommends waiting before publishing
                time.sleep(1)
                result = self._publish_container(creation_id)
                logger.info("Threads post published (attempt %d): id=%s", attempt, result.get("id"))
                return result
            except Exception as e:
                last_err = e
                logger.warning("Attempt %d to post to Threads failed: %s", attempt, e)
                if attempt < attempts:
                    time.sleep(backoff)
                    backoff *= 2

        logger.error("Failed to post to Threads after %d attempts", attempts)
        raise last_err

    def get_me(self) -> Dict:
        """Return basic info about the authenticated Threads user."""
        url = f"{THREADS_API_BASE}/me"
        resp = requests.get(url, params={"access_token": self.access_token}, timeout=10)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    try:
        tc = ThreadsClient()
        me = tc.get_me()
        print("Authenticated as:", me)
    except Exception as e:
        print("Threads client setup failed:", e)
