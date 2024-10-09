#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""retweets.py: Implementation of Twitter retweeted_by endpoint.

"With the Retweets lookup endpoint, you can retrieve a list of accounts that have Retweeted a Tweet. For this endpoint, pagination tokens will be provided for
paging through large sets of results in batches of up to 100 users. "
(Source: https://developer.twitter.com/en/docs/twitter-api/tweets/retweets/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get User that retweeted a specific tweet::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.retweets import get_retweets

        async for user in get_retweets('1679113508724539393'):
            print(user.model_dump_json())
"""

import asyncio
import logging
import os
from typing import AsyncGenerator, Dict, Optional

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsIdRetweetedByResponse, User
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import TWEET_FIELDS, USER_EXPANSIONS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_retweets(id: str) -> AsyncGenerator[User, None]:
    """Asynchronously retrieves users who have retweeted a specified tweet.

    This function queries the Twitter API to find users who have retweeted the tweet corresponding to the given ID. It handles rate limiting using an internal
    instance of RateLimiter, automatically pausing requests if the rate limit is exceeded. The function also handles pagination automatically if there are more
    results than can be returned in a single response.

    Args:
        id (str): The ID of the tweet for which to retrieve retweeters.

    Yields:
        User: An object representing a Twitter user who has retweeted the specified tweet.

    Raises:
        Exception: If an HTTP error occurs that prevents retrieving the retweets or if the tweet ID is invalid.

    Note:
        The function automatically handles pagination of results using the 'next_token' provided by Twitter's API response.
    """
    rate_limiter = RateLimiter()
    pagination_token: Optional[str] = None
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": USER_EXPANSIONS,
            "user.fields": USER_FIELDS,
            "max_results": str(100),  # Max results per response
        }

        while True:
            if pagination_token:
                params["pagination_token"] = pagination_token

            logger.debug(f"search recent params={params}")
            async with session.get(f"https://api.twitter.com/2/tweets/{id}/retweeted_by", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot search retweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot search retweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()

                for user in response_json.get("data", []):
                    yield User.model_validate(user)

                try:
                    Get2TweetsIdRetweetedByResponse.model_validate(response_json)
                except Exception as e:
                    logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                    # logger.warning(response_text)

                if "next_token" in response_json.get("meta"):
                    params["pagination_token"] = response_json.get("meta").get("next_token")
                else:
                    break
