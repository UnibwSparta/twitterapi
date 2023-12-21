#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""full_seach.py: Implementation of Twitter Full-archive search endpoint.

"The v2 full-archive search endpoint is only available to Projects with Academic Research access. The endpoint allows you to programmatically access
public Tweets from the complete archive dating back to the first Tweet in March 2006, based on your search query."
(Source: https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get Tweets from full search::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from datetime import datetime
        from sparta.twitterapi.tweets.full_search import get_full_search

        query = '(#test OR @projekt_sparta) -is:retweet'
        starttime = datetime(2021, 6, 1, 0, 0)
        endtime = datetime(2021, 10, 4, 0, 0)

        async for tweet_response in get_full_search(query=query, start_time=starttime, end_time=endtime):
            print(json.dumps(tweet_response.tweet))
            print(json.dumps(tweet_response.includes))

    Get estimated number for full search query::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from datetime import datetime
        from sparta.twitterapi.tweets.full_search import get_full_search_count

        query = '(#test OR @projekt_sparta) -is:retweet'
        starttime = datetime(2021, 6, 1, 0, 0)
        endtime = datetime(2021, 10, 4, 0, 0)

        count = sum(
            [count.tweet_count async for count in get_full_search_count(query=query, start_time=starttime, end_time=endtime, granularity="day")]
        )
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsCountsAllResponse, SearchCount
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_full_search(
    query: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
    sort_order: str = None,
) -> AsyncGenerator[TweetResponse, None]:
    """Asynchronously retrieves tweets that match a specified search query.

    This function queries the Twitter API to find tweets matching the given search criteria. It handles rate limiting using an internal instance of
    RateLimiter, automatically pausing requests if the rate limit is exceeded.

    Args:
        query (str): The search query for matching Tweets. Refer to Twitter API documentation for details on query format and limitations.
        start_time (datetime, optional): The oldest UTC timestamp from which tweets will be provided. Inclusive and in second granularity.
        end_time (datetime, optional): The newest UTC timestamp to which tweets will be provided. Exclusive and in second granularity.
        since_id (str, optional): Returns results with a Tweet ID greater than this ID.
        until_id (str, optional): Returns results with a Tweet ID less than this ID.
        sort_order (str, optional): The order in which to return results (e.g., 'recency' or 'relevancy').

    Yields:
        TweetResponse: An object representing the tweet data for each tweet that matches the query.

    Raises:
        Exception: If an HTTP error occurs that prevents retrieving the tweets or if the query parameters are invalid.

    Note:
        The function automatically handles pagination of results using the 'next_token' provided by Twitter's API response.
    """
    rate_limiter = RateLimiter()
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
            logger.debug(f"search recent params={params}")
            async with session.get("https://api.twitter.com/2/tweets/search/all", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot search full tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot search full tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()

                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

                if "next_token" in response_json.get("meta"):
                    params["next_token"] = response_json.get("meta").get("next_token")
                else:
                    break


async def get_full_search_count(
    query: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
    granularity: str = "hour",
) -> AsyncGenerator[SearchCount, None]:
    """Asynchronously retrieves the count of tweets matching a specified search query, aggregated according to a specified granularity (e.g., hourly).

    This function queries the Twitter API to count tweets matching the given search criteria and aggregates the counts based on the specified granularity.
    It handles rate limiting using an internal instance of RateLimiter, automatically pausing requests if the rate limit is exceeded.

    Args:
        query (str): The search query for matching Tweets. Refer to Twitter API documentation for query format and limitations.
        start_time (datetime, optional): The oldest UTC timestamp from which tweet counts will be provided. Inclusive and in second granularity.
        end_time (datetime, optional): The newest UTC timestamp to which tweet counts will be provided. Exclusive and in second granularity.
        since_id (str, optional): Returns results with a Tweet ID greater than this ID.
        until_id (str, optional): Returns results with a Tweet ID less than this ID.
        granularity (str, optional): The granularity for the search counts results ('minute', 'hour', or 'day'). Defaults to 'hour'.

    Yields:
        SearchCount: An object representing the tweet count data for each interval according to the specified granularity.

    Raises:
        Exception: If an invalid granularity is specified or if an HTTP error occurs that prevents retrieving the tweet counts.

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
            async with session.get("https://api.twitter.com/2/tweets/counts/all", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot get full tweet count (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot search full tweet counts (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                counts = Get2TweetsCountsAllResponse.model_validate_json(await response.text())
                if counts.data:
                    for count in counts.data:
                        yield count

                if counts.meta and counts.meta.next_token:
                    params["next_token"] = counts.meta.next_token
                else:
                    break
