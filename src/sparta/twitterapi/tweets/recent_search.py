#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""recent_search.py: Implementation of Twitter recent search endpoint.

"The recent search endpoint allows you to programmatically access filtered public Tweets posted over the last week, and is available to all developers who
have a developer account and are using keys and tokens from an App within a Project."
(Source: https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get Tweets from recent search::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from datetime import datetime
        from sparta.twitterapi.tweets.recent_search import get_recent_search

        query = '(#test OR @projekt_sparta) -is:retweet'
        starttime = datetime(2022, 12, 21, 0, 0)
        endtime = datetime(2022, 12, 24, 0, 0)

        async for tweet_response in get_recent_search(query=query, start_time=starttime, end_time=endtime):
            print(json.dumps(tweet_response.tweet))
            print(json.dumps(tweet_response.includes))

    Get estimated number for recent search query::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from datetime import datetime
        from sparta.twitterapi.tweets.recent_search import get_recent_search_count

        query = '(#test OR @projekt_sparta) -is:retweet'
        starttime = datetime(2022, 12, 21, 0, 0)
        endtime = datetime(2022, 12, 24, 0, 0)

        count = sum(
            [count.tweet_count async for count in get_recent_search_count(query=query, start_time=starttime, end_time=endtime, granularity="day")]
        )
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, Optional

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsCountsRecentResponse, SearchCount
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_recent_search(
    query: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
    sort_order: str = None,
) -> AsyncGenerator[TweetResponse, None]:
    """Asynchronously retrieves tweets from the last 7 days that match the specified query.

    This function queries the Twitter API to find tweets matching the given search criteria within the last 7 days. It uses an internal instance of
    RateLimiter to handle rate limiting, automatically pausing requests if the rate limit is exceeded.

    Args:
        query (str): The search query for matching Tweets. Refer to https://t.co/rulelength to identify the max query length. How to build a rule:
        https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule
        start_time (datetime, optional): The oldest UTC timestamp from which tweets will be provided. Inclusive and in second granularity.
        end_time (datetime, optional): The newest UTC timestamp to which tweets will be provided. Exclusive and in second granularity.
        since_id (str, optional): Returns results with a Tweet ID greater than this ID.
        until_id (str, optional): Returns results with a Tweet ID less than this ID.
        sort_order (str, optional): The order in which to return results (e.g., 'recency' or 'relevancy'). Defaults to None.

    Yields:
        TweetResponse: An object representing the tweet data for each tweet that matches the query.

    Raises:
        Exception: If an HTTP error occurs that prevents retrieving the tweets or if the query parameters are invalid.

    Note:
        The function automatically handles pagination of results using the 'next_token' provided by Twitter's API response.
    """

    rate_limiter = RateLimiter()
    next_token: Optional[str] = None
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "query": query,
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
            "media.fields": MEDIA_FIELDS,
            "poll.fields": POLL_FIELDS,
            "place.fields": PLACE_FIELDS,
            "max_results": str(100),  # Max results per response
        }

        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if sort_order:
            params["sort_order"] = sort_order

        while True:
            if next_token:
                params["next_token"] = next_token

            logger.debug(f"search recent params={params}")
            async with session.get("https://api.twitter.com/2/tweets/search/recent", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()

                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

                if "next_token" in response_json.get("meta"):
                    params["next_token"] = response_json.get("meta").get("next_token")
                else:
                    break


async def get_recent_search_count(
    query: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
    granularity: str = None,
) -> AsyncGenerator[SearchCount, None]:
    """Asynchronously retrieves the count of tweets matching a specified search query from the last 7 days, aggregated according to a specified granularity.

    This function queries the Twitter API to count tweets matching the given search criteria within the last 7 days and aggregates the counts based on the
    specified granularity. It uses an internal instance of RateLimiter to handle rate limiting, automatically pausing requests if the rate limit is exceeded.

    Args:
        query (str): The search query for matching Tweets. Refer to https://t.co/rulelength to identify the max query length. How to build a rule:
        https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule
        start_time (datetime, optional): The oldest UTC timestamp from which tweet counts will be provided. Inclusive and in second granularity.
        end_time (datetime, optional): The newest UTC timestamp to which tweet counts will be provided. Exclusive and in second granularity.
        since_id (str, optional): Returns results with a Tweet ID greater than this ID.
        until_id (str, optional): Returns results with a Tweet ID less than this ID.
        granularity (str, optional): The granularity for the search counts results (e.g., 'minute', 'hour', or 'day').

    Yields:
        SearchCount: An object representing the tweet count data for each interval according to the specified granularity.

    Raises:
        Exception: If an invalid granularity is specified, if an HTTP error occurs that prevents retrieving the tweet counts, or if the query parameters are
        invalid.

    Note:
        The function automatically handles pagination of results using the 'next_token' provided by Twitter's API response.
    """

    if granularity not in ["minute", "hour", "day"]:
        raise Exception(f"Wrong granularity. Given granularity: {granularity}. Possible values = minute, hour, day")

    rate_limiter = RateLimiter()
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "query": query,
        }
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if granularity:
            params["granularity"] = granularity

        while True:
            logger.debug(f"search recent params={params}")
            async with session.get("https://api.twitter.com/2/tweets/counts/recent", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot get recent tweet counts (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot get recent tweet counts (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_text = await response.text()
                response_json = json.loads(response_text)

                counts = Get2TweetsCountsRecentResponse.model_validate(response_json)
                if counts.data:
                    for count in counts.data:
                        yield count

                if counts.meta and counts.meta.next_token:
                    params["next_token"] = counts.meta.next_token
                else:
                    break
