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
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.rate_limiter import RateLimiter

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
    """Asynchronously retrieves tweets quoting a specified tweet.

    This function queries the Twitter API to find tweets that are quote tweets of the tweet corresponding to the given ID. It handles rate limiting using an
    internal instance of RateLimiter, automatically pausing requests if the rate limit is exceeded. The function also supports time-based filtering and
    pagination.

    Args:
        id (str): The ID of the tweet for which to retrieve quote tweets.
        start_time (datetime, optional): The oldest UTC timestamp from which quote tweets will be provided. Inclusive and in second granularity.
        end_time (datetime, optional): The newest UTC timestamp to which quote tweets will be provided. Exclusive and in second granularity.
        since_id (str, optional): Returns quote tweets with an ID greater than this ID.
        until_id (str, optional): Returns quote tweets with an ID less than this ID.

    Yields:
        TweetResponse: An object representing a tweet that quotes the specified tweet.

    Raises:
        Exception: If an HTTP error occurs that prevents retrieving the quote tweets or if the tweet ID is invalid.

    Note:
        The function automatically handles pagination of results using the 'next_token' provided by Twitter's API response.
    """
    rate_limiter = RateLimiter()
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

                # try:
                #     Get2TweetsIdQuoteTweetsResponse.model_validate(response_json)
                # except Exception as e:
                #     logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                #     # logger.warning(response_text)
                try:
                    if "errors" in response_json:
                        logger.warning(f'Errors: {response_json["errors"]}')
                    if "next_token" in response_json.get("meta", {}):
                        params["pagination_token"] = response_json.get("meta")
                    else:
                        break
                except Exception as e:
                    logger.warning(e)
                    logger.warning(response_json)
                    raise Exception
