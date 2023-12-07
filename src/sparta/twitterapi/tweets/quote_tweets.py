#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""quote_tweets.py: Implementation of Twitter Quote Tweets lookup endpoint.

"The Quote Tweets lookup endpoint gives the Quote Tweets for a given Tweet ID.  This allows developers that build apps and clients to get the Quote Tweets for
a Tweet quickly and efficiently. It also makes it easy for researchers to study the full conversation around a Tweet including all its Quote Tweets."
(Source: https://developer.twitter.com/en/docs/twitter-api/tweets/quote-tweets/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get quoted Tweets::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.quote_tweets import get_quote_tweets

        tweet_ids = ['1511275800758300675', '1594704992480690178']

        for tweet_id in tweet_ids:
            async for tweet_response in get_quote_tweets(tweet_id):
                print(json.dumps(tweet_response.tweet))
                print(json.dumps(tweet_response.includes))
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse

# from sparta.twitterapi.models.twitter_v2_spec import Get2TweetsIdQuoteTweetsResponse
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_quote_tweets(
    id: str,
    start_time: datetime = None,
    end_time: datetime = None,
    since_id: str = None,
    until_id: str = None,
) -> AsyncGenerator[TweetResponse, None]:
    """Returns quoted Tweets.

    Args:
        id (str): A tweet ID for which to retrieve quote tweets.
        start_time (datetime): The oldest UTC timestamp from which the Tweets will be provided. Timestamp is in second granularity and is inclusive
            (i.e. 12:00:01 includes the first second of the minute). Defaults to None.
        end_time (datetime): The newest, most recent UTC timestamp to which the Tweets will be provided. Timestamp is in second granularity and is exclusive
            (i.e. 12:00:01 excludes the first second of the minute). Defaults to None.
        since_id (str, optional): Returns results with a Tweet ID greater than (that is, more recent than) the specified ID. Defaults to None.
        until_id (str, optional): Returns results with a Tweet ID less than (that is, older than) the specified ID. Defaults to None.


    Raises:
        Exception: Cannot get the search result due to an http error.

    Returns:
        AsyncGenerator[TweetResponse, None]: AsyncGenerator that yields TweetResponses.

    Yields:
        Iterator[AsyncGenerator[TweetResponse, None]]: A TweetResponse Object.
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
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

        while True:
            logger.debug(f"search recent params={params}")
            async with session.get(f"https://api.twitter.com/2/tweets/{id}/quote_tweets", params=params) as response:
                if response.status == 400:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    raise Exception

                if response.status == 429:
                    logger.warn(f"{response.status} Too Many Requests. Sleep for 1 minute...")
                    await asyncio.sleep(60)
                    continue
                if not response.ok:
                    logger.error(f"Cannot search recent tweets (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(5)
                    continue

                response_text = await response.text()
                response_json = json.loads(response_text)

                for tweet in response_json.get("data", []):
                    yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))

                # try:
                #     Get2TweetsIdQuoteTweetsResponse(**response_json)
                # except Exception as e:
                #     logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                #     # logger.warn(response_text)
                try:
                    if "errors" in response_json:
                        logger.warn(f'Errors: {response_json["errors"]}')
                    if "next_token" in response_json.get("meta", {}):
                        params["pagination_token"] = response_json["meta"]["next_token"]
                    else:
                        break
                except Exception as e:
                    logger.warn(e)
                    logger.warn(response_json)
                    raise Exception
