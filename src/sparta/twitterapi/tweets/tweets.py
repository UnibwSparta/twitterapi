#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tweets.py: Implementation of Twitter tweets endpoint.

"While there are a variety of different HTTP, selection, and delivery methods that can deliver, publish, and act upon Tweets, this group of REST endpoints
simply returns a Tweet or group of Tweets, specified by a Tweet ID. While simple, these endpoints can be used to receive up-to-date details on a Tweet,
verify that a Tweet is available, and examine its edit history. These endpoints are also important tools for managing compliance events."
(Source: https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get Tweets by ID::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.tweets import get_tweets_by_id

        async for tweet_response in get_tweets_by_id(['1511275800758300675', '1546866845180887040']):
            print(json.dumps(tweet_response.tweet))
            print(json.dumps(tweet_response.includes))
"""

import logging
import os
from typing import AsyncGenerator, Dict, List

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_tweets_by_id(ids: List[str]) -> AsyncGenerator[TweetResponse, None]:
    """Asynchronously retrieves tweets by their IDs.

    This function handles the retrieval of tweets from Twitter's API based on a list of tweet IDs. It respects the rate limiting by utilizing an internal
    RateLimiter instance. If the rate limit is exceeded, the function will automatically wait until it can proceed with requests.

    Args:
        ids (List[str]): A list of tweet IDs for which to retrieve tweets. Up to 100 IDs can be included in a single request.

    Returns:
        AsyncGenerator[TweetResponse, None]: An asynchronous generator that yields TweetResponse objects for each tweet.

    Raises:
        Exception: If an HTTP error occurs that prevents retrieving the tweets.

    Yields:
        TweetResponse: An object representing the tweet data for each given tweet ID.
    """
    rate_limiter = RateLimiter()
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "ids": ",".join(ids),
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
            "media.fields": MEDIA_FIELDS,
            "poll.fields": POLL_FIELDS,
            "place.fields": PLACE_FIELDS,
        }
        logger.debug(f"search recent params={params}")
        while True:
            async with session.get("https://api.twitter.com/2/tweets", params=params) as response:
                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    raise Exception(f"Cannot search tweets {params} (HTTP {response.status}): {await response.text()}")

                response_json = await response.json()

                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

            break
