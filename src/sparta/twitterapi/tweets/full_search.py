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
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsCountsAllResponse, SearchCount
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
    """Returns Tweets that match a search query. If no time or id parameters are specified, the last 30 days are assumed.

    Args:
        query (str): One query/rule/filter for matching Tweets. Refer to https://t.co/rulelength to identify the max query length.
            How to build a rule: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule
        start_time (datetime): The oldest UTC timestamp from which the Tweets will be provided. Timestamp is in second granularity and is inclusive
            (i.e. 12:00:01 includes the first second of the minute). Defaults to None.
        end_time (datetime): The newest, most recent UTC timestamp to which the Tweets will be provided. Timestamp is in second granularity and is exclusive
            (i.e. 12:00:01 excludes the first second of the minute). Defaults to None.
        since_id (str, optional): Returns results with a Tweet ID greater than (that is, more recent than) the specified ID. Defaults to None.
        until_id (str, optional): Returns results with a Tweet ID less than (that is, older than) the specified ID. Defaults to None.
        sort_order (str, optional): This order in which to return results. Possible options: recency and relevancy. Defaults to None.


    Raises:
        Exception: Cannot get the search result due to an http error.

    Returns:
        AsyncGenerator[TweetResponse, None]: AsyncGenerator that yields TweetResponses.

    Yields:
        Iterator[AsyncGenerator[TweetResponse, None]]: A TweetResponse Object.
    """
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
                    logger.error(f"Cannot search tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                if response.status == 429:
                    logger.warn(f"{response.status} Too Many Requests. Sleep for 5 second...")
                    await asyncio.sleep(5)
                    continue
                if not response.ok:
                    logger.error(f"Cannot search tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(5)
                    continue

                response_text = await response.text()
                response_json = json.loads(response_text)

                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

                # try:
                #     Get2TweetsSearchAllResponse.model_validate(response_json)
                # except Exception as e:
                #     logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                #     # logger.warn(response_text)

                if "next_token" in response_json["meta"]:
                    params["next_token"] = response_json["meta"]["next_token"]
                else:
                    return


async def get_full_search_count(
    query: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
    granularity: str = "hour",
) -> AsyncGenerator[SearchCount, None]:
    """Returns the number of tweets that match a query according to a granularity (e.g. hourwise) over a given time period. If no time or id parameters are
    specified, the last 30 days are assumed.

    Args:
        query (str): One query/rule/filter for matching Tweets. Refer to https://t.co/rulelength to identify the max query length.
            How to build a rule: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule
        start_time (datetime): The oldest UTC timestamp from which the Tweets will be provided. Timestamp is in second granularity and is inclusive
            (i.e. 12:00:01 includes the first second of the minute). Defaults to None.
        end_time (datetime): The newest, most recent UTC timestamp to which the Tweets will be provided. Timestamp is in second granularity and is exclusive
            (i.e. 12:00:01 excludes the first second of the minute). Defaults to None.
        since_id (str, optional): Returns results with a Tweet ID greater than (that is, more recent than) the specified ID.  Defaults to None.
        until_id (str, optional): Returns results with a Tweet ID less than (that is, older than) the specified ID.  Defaults to None.
        granularity (str, optional): The granularity for the search counts results. Defaults to 'hour'

    Returns:
        AsyncGenerator[SearchCount, None]: AsyncGenerator that yields a Twitter SearchCounts.

    Yields:
        Iterator[AsyncGenerator[SearchCount, None]]: A Twitter SearchCount Object.
    """
    if granularity not in ["minute", "hour", "day"]:
        raise Exception(f"Wrong granularity. Given granularity: {granularity}. Possible values = minute, hour, day")

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
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                if response.status == 429:
                    logger.warn("429 Too Many Requests.")
                    await asyncio.sleep(5)
                    continue

                if not response.ok:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(5)
                    continue

                counts = Get2TweetsCountsAllResponse.model_validate_json(await response.text())
                if counts.data:
                    for count in counts.data:
                        yield count

                if counts.meta and counts.meta.next_token:
                    params["next_token"] = counts.meta.next_token
                else:
                    return
