#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""timeline.py: Implementation of User Post Timeline endpoint.

The User Post Timeline endpoint allows developers to retrieve recent Posts, Retweets, replies, and Quote Tweets from a specified user.

Endpoint documentation:
https://developer.x.com/en/docs/x-api/tweets/timelines/introduction

Example:
    import os
    import json
    os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
    from datetime import datetime
    from sparta.twitterapi.timeline import get_user_timeline_by_id

    user_id = "2244994945"
    start_time = datetime(2021, 6, 1)
    end_time = datetime(2021, 10, 1)
    async for tweet_response in get_user_timeline_by_id(user_id, start_time=start_time, end_time=end_time, exclude=["replies", "retweets"]):
        print(json.dumps(tweet_response.tweet))
        print(json.dumps(tweet_response.includes))
)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_user_timeline_by_id(
    user_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    since_id: Optional[str] = None,
    until_id: Optional[str] = None,
    exclude: Optional[List[str]] = None,
) -> AsyncGenerator[TweetResponse, None]:
    """Asynchronously retrieves Posts from a user's timeline.

    Args:
        user_id (str): The ID of the user.
        start_time (datetime, optional): Earliest datetime for Posts.
        end_time (datetime, optional): Latest datetime for Posts.
        since_id (str, optional): Returns results with Post ID greater than this ID.
        until_id (str, optional): Returns results with Post ID less than this ID.
        exclude (List[str], optional): Entities to exclude, e.g., ["replies", "retweets"].

    Yields:
        TweetResponse: Individual Posts with associated data and includes.

    Raises:
        Exception: If an HTTP error occurs or if request parameters are invalid.
    """
    rate_limiter = RateLimiter()
    url = f"https://api.x.com/2/users/{user_id}/tweets"

    async with aiohttp.ClientSession(headers=headers) as session:
        params = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
            "media.fields": MEDIA_FIELDS,
            "poll.fields": POLL_FIELDS,
            "place.fields": PLACE_FIELDS,
            "max_results": str(100),
        }

        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if exclude:
            params["exclude"] = ",".join(exclude)

        while True:
            logger.debug(f"Requesting timeline for user_id={user_id} with params={params}")
            async with session.get(url, params=params) as response:
                if response.status == 400:
                    logger.error(f"Bad request for timeline (HTTP {response.status}): {await response.text()}")
                    raise Exception("Invalid request parameters.")

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Error fetching timeline (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()
                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

                if "next_token" in response_json.get("meta"):
                    params["next_token"] = response_json.get("meta").get("next_token")
                else:
                    break
