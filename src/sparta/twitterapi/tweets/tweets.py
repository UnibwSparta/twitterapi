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

import json
import logging
import os
from typing import AsyncGenerator, Dict, List

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_tweets_by_id(ids: List[str]) -> AsyncGenerator[TweetResponse, None]:
    """Returns Tweets specified by the requested ID.

    Args:
        ids (List[str]): A list of Tweet IDs. Up to 100 are allowed in a single request.

    Raises:
        Exception: Cannot get the search result due to an http error.

    Returns:
        AsyncGenerator[TweetResponse, None]: AsyncGenerator that yields TweetResponses.

    Yields:
        Iterator[AsyncGenerator[TweetResponse, None]]: A TweetResponse Object.
    """
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
        async with session.get("https://api.twitter.com/2/tweets", params=params) as response:
            if not response.ok:
                raise Exception(f"Cannot search tweets {params} (HTTP {response.status}): {await response.text()}")

            response_text = await response.text()
            response_json = json.loads(response_text)

            for tweet in response_json.get("data", []):
                yield TweetResponse(tweet=tweet, includes=response_json.get("includes", {}))
                try:
                    # Get2TweetsResponse.model_validate(response_json)
                    pass
                except Exception as e:
                    logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                    logger.warn(response_text)
