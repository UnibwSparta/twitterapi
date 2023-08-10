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
import json
import logging
import os
from typing import AsyncGenerator, Dict, Optional

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsIdRetweetedByResponse, User
from sparta.twitterapi.tweets.constants import TWEET_FIELDS, USER_EXPANSIONS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_retweets(id: str) -> AsyncGenerator[User, None]:
    """Get tweets from the last 7 days (maximum) that match the query.

    Args:
        id (str): "A single Tweet ID.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.

    Returns:
        AsyncGenerator[User, None]: AsyncGenerator that yields Twitter User objects.

    Yields:
        Iterator[AsyncGenerator[User, None]]: A Twitter User object.
    """
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
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                if response.status == 429:
                    logger.warn("429 Too Many Requests. Sleep for 5 second...")
                    await asyncio.sleep(5)
                    continue
                if not response.ok:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(5)
                    continue

                response_text = await response.text()
                response_json = json.loads(response_text)

                for user in response_json.get("data", []):
                    yield User.model_validate(user)

                try:
                    Get2TweetsIdRetweetedByResponse(**response_json)
                except Exception as e:
                    logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                    # logger.warn(response_text)

                if "next_token" in response_json["meta"]:
                    params["pagination_token"] = response_json["meta"]["next_token"]
                else:
                    return
