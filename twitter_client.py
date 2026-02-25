from dotenv import load_dotenv
import os
import time
import logging
from typing import Dict, Optional

load_dotenv()

logger = logging.getLogger(__name__)

try:
    import tweepy
except Exception:
    tweepy = None


class TwitterClient:
    """Simple Twitter client using tweepy.Client for v2 endpoints.

    Requires the following environment variables (or values passed to the constructor):
      - TWITTER_API_KEY
      - TWITTER_API_KEY_SECRET
      - TWITTER_ACCESS_TOKEN
      - TWITTER_ACCESS_TOKEN_SECRET
    """

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ):
        if tweepy is None:
            raise RuntimeError("tweepy is not installed; add it to requirements.txt and install dependencies")

        self.consumer_key = consumer_key or os.getenv("TWITTER_API_KEY")
        self.consumer_secret = consumer_secret or os.getenv("TWITTER_API_KEY_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        missing = [
            name
            for name, val in (
                ("TWITTER_API_KEY", self.consumer_key),
                ("TWITTER_API_KEY_SECRET", self.consumer_secret),
                ("TWITTER_ACCESS_TOKEN", self.access_token),
                ("TWITTER_ACCESS_TOKEN_SECRET", self.access_token_secret),
            )
            if not val
        ]

        if missing:
            raise EnvironmentError(f"Missing Twitter credentials: {', '.join(missing)}")

        # Create a tweepy.Client instance that can create tweets using OAuth 1.0a credentials
        self.client = tweepy.Client(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True,
        )

    def post_tweet(self, text: str) -> Dict:
        """Post a text-only tweet. Returns the API response data."""
        # Retry logic with simple exponential backoff
        attempts = 3
        backoff = 1
        last_err = None
        for attempt in range(1, attempts + 1):
            try:
                resp = self.client.create_tweet(text=text)
                logger.info("Tweet posted (attempt %d)", attempt)
                return resp.data if hasattr(resp, "data") else resp
            except Exception as e:
                last_err = e
                logger.warning("Attempt %d to post tweet failed: %s", attempt, e)
                if attempt < attempts:
                    time.sleep(backoff)
                    backoff *= 2
        # all attempts failed
        logger.error("Failed to post tweet after %d attempts", attempts)
        raise last_err

    def reply(self, text: str, in_reply_to_tweet_id: str) -> Dict:
        """Reply to an existing tweet id."""
        try:
            resp = self.client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id)
            return resp.data if hasattr(resp, "data") else resp
        except Exception as e:
            logger.exception("Failed to send reply: %s", e)
            raise

    def get_me(self) -> Dict:
        """Return the authenticated user information."""
        try:
            resp = self.client.get_me()
            return resp.data if hasattr(resp, "data") else resp
        except Exception as e:
            logger.exception("Failed to fetch authenticated user: %s", e)
            raise


if __name__ == "__main__":
    # Quick local smoke test (requires proper env vars)
    try:
        tc = TwitterClient()
        me = tc.get_me()
        print("Authenticated as:", me)
    except Exception as e:
        print("Twitter client setup failed:", e)
