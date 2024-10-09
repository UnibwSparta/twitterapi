#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""user.py: Implementation of Twitter Follower lookup endpoint.

"The follows lookup endpoints enable you to explore and analyze relationships between users, which is sometimes called network analysis. Specifically, there are
two REST endpoints that return user objects representing who a specified user is following, or who is following a specified user."
(Source: https://developer.twitter.com/en/docs/twitter-api/users/follows/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get followers by id::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.users.follower import get_followers_by_id

        async for user in get_followers_by_id('1422600096324231168'):
            print(user.model_dump_json())


    Get following by id::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.users.follower import get_following_by_id

        async for user in get_following_by_id('1422600096324231168'):
            print(user.model_dump_json())
"""

import asyncio
import logging
import os
from typing import AsyncGenerator, Dict

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2UsersIdFollowersResponse, User
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_followers_by_id(id: str, max_resulsts: int = 1000) -> AsyncGenerator[User, None]:
    """Returns Users who are followers of the specified User ID.

    Args:
        id (str): The ID of the User to lookup.
        max_resulsts (int, optional): The maximum number of results. Defaults to 1000.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.

    Returns:
        AsyncGenerator[User, None]: AsyncGenerator that yields Twitter User objects.

    Yields:
        Iterator[AsyncGenerator[User, None]]: A Twitter User object.
    """
    rate_limiter = RateLimiter()
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "user.fields": USER_FIELDS,
            # "tweet.fields": tweet_fields,
            # "expansions": user_expansions,
            "max_results": str(max_resulsts),  # Max results per response
        }

        while True:
            logger.debug(f"Search users params={params}")
            async with session.get(f"https://api.twitter.com/2/users/{id}/followers", params=params) as response:
                if response.status in [400, 401, 402, 403, 404]:
                    logger.error(f"Cannot get followers for user {id} (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot get followers for user {id} with params: {params} (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()

                try:
                    users = Get2UsersIdFollowersResponse.model_validate(response_json)
                except Exception as e:
                    logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                    logger.warning(response_json)

                if not users.data:
                    raise Exception(users)

                for user in users.data:
                    yield user

                if "next_token" in response_json.get("meta"):
                    params["pagination_token"] = response_json.get("meta").get("next_token")
                else:
                    break


async def get_following_by_id(id: str, max_resulsts: int = 1000) -> AsyncGenerator[User, None]:
    """Returns Users that are being followed by the provided User ID.

    Args:
        id (str): The ID of the User to lookup.
        max_resulsts (int, optional): The maximum number of results. Defaults to 1000.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.

    Returns:
        AsyncGenerator[User, None]: AsyncGenerator that yields Twitter User objects.

    Yields:
        Iterator[AsyncGenerator[User, None]]: A Twitter User object.
    """
    rate_limiter = RateLimiter()
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "user.fields": USER_FIELDS,
            # "tweet.fields": tweet_fields,
            # "expansions": user_expansions,
            "max_results": str(max_resulsts),  # Max results per response
        }

        while True:
            logger.debug(f"Search users params={params}")
            async with session.get(f"https://api.twitter.com/2/users/{id}/following", params=params) as response:
                if response.status in [400, 401, 402, 403, 404]:
                    logger.error(f"Cannot get followed users for {id} (HTTP {response.status}): {await response.text()}")
                    raise Exception

                rate_limiter.update_limits(dict(response.headers))

                if response.status == 429:
                    await rate_limiter.wait_for_limit_reset()
                    continue

                if not response.ok:
                    logger.error(f"Cannot get followed users for {id} with params: {params} (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()

                try:
                    users = Get2UsersIdFollowersResponse.model_validate(response_json)
                except Exception as e:
                    logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                    logger.warning(response_json)

                if not users.data:
                    raise Exception(users)

                for user in users.data:
                    yield user

                if "next_token" in response_json.get("meta"):
                    params["pagination_token"] = response_json.get("meta").get("next_token")
                else:
                    break
