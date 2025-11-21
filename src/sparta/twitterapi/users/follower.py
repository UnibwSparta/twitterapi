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

from sparta.twitterapi.models.twitter_v2_spec import Get2UsersIdFollowersResponse, Get2UsersIdFollowingResponse, User
from sparta.twitterapi.rate_limiter import RateLimiter
from sparta.twitterapi.tweets.constants import USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_followers_by_id(
    id: str,
    max_results: int = 1000,
    raise_exception_on_http_503: bool = False,
    raise_exception_on_model_validation_error: bool = False,
    sleep_time_on_not_ok: int = 10,
    num_tries_on_not_ok: int = -1,
) -> AsyncGenerator[User, None]:
    """Returns Users who are followers of the specified User ID.

    Args:
        id (str): The ID of the User to lookup.
        max_results (int, optional): The maximum number of results. Defaults to 1000.
        raise_exception_on_http_503 (bool, optional): Whether to raise an exception on HTTP 503 errors.
            If False, then wait until HTTP 503 resolves, which is better suitable in case of live streaming.
            True, is more suitable for batch processing. Defaults to False.
            NOTE: In some cases, the Twitter API returns HTTP 503 errors during pagination, which may be transient, but still block live streaming.
        raise_exception_on_model_validation_error (bool, optional): Whether to raise an exception on model validation errors.
            If False, then only logs warnings, which is better suitable in case of live streaming.
            True, is more suitable for batch processing. Defaults to False.
        sleep_time_on_not_ok (int, optional): The sleep time in seconds to wait before retrying after an HTTP error. Defaults to 10.
        num_tries_on_not_ok (int, optional): The number of tries to attempt after an HTTP error.
            If -1, then unlimited. Defaults to -1.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.
        Exception: HTTP 503 error.
        Exception: Model validation error.

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
            "max_results": str(max_results),  # Max results per response
        }

        num_tries_on_not_ok_i = num_tries_on_not_ok + 1
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

                response_text = await response.text()
                response_json = await response.json()
                if not response.ok:
                    logger.error(
                        f"Cannot get followers for user {id} with params: {params} (HTTP {response.status}): {response_text}. Response JSON: {response_json}"
                    )

                    # Raise exception on HTTP 503 if specified
                    if response.status == 503 and raise_exception_on_http_503:
                        raise Exception(response_json)

                    # Note: From experience, only HTTP 503 errors can appear here
                    # Decrement the number of tries left on HTTP error
                    if num_tries_on_not_ok_i > 0:
                        num_tries_on_not_ok_i -= 1

                    # Infinite or remaining tries on HTTP error
                    if num_tries_on_not_ok_i < 0 or num_tries_on_not_ok_i > 0:
                        await asyncio.sleep(sleep_time_on_not_ok)
                        continue

                    # num_tries_on_not_ok_i == 0, no more tries left, break the loop and return
                    else:
                        logger.error(f"Exceeded number of tries ({num_tries_on_not_ok}) on HTTP error for getting followers of user {id}.")
                        break

                try:
                    users = Get2UsersIdFollowersResponse.model_validate(response_json)
                except Exception as e:
                    if not raise_exception_on_model_validation_error:
                        logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                        logger.warning(response_json)
                    else:
                        # Concatenate all lines of e_str into one line
                        e_str = str(e)
                        e_str = " | ".join(e_str.splitlines())
                        raise Exception(f"Inconsistent twitter OpenAPI documentation {e_str} for response: {response_json}")

                if not users.data:
                    raise Exception(users)

                for user in users.data:
                    yield user

                if "next_token" in response_json.get("meta"):
                    params["pagination_token"] = response_json.get("meta").get("next_token")
                else:
                    break


async def get_following_by_id(
    id: str,
    max_results: int = 1000,
    raise_exception_on_http_503: bool = False,
    raise_exception_on_model_validation_error: bool = False,
    sleep_time_on_not_ok: int = 10,
    num_tries_on_not_ok: int = -1,
) -> AsyncGenerator[User, None]:
    """Returns Users that are being followed by the provided User ID.

    Args:
        id (str): The ID of the User to lookup.
        max_results (int, optional): The maximum number of results. Defaults to 1000.
        raise_exception_on_http_503 (bool, optional): Whether to raise an exception on HTTP 503 errors.
            If False, then wait until HTTP 503 resolves, which is better suitable in case of live streaming.
            True, is more suitable for batch processing. Defaults to False.
            NOTE: In some cases, the Twitter API returns HTTP 503 errors during pagination, which may be transient, but still block live streaming.
        raise_exception_on_model_validation_error (bool, optional): Whether to raise an exception on model validation errors.
            If False, then only logs warnings, which is better suitable in case of live streaming.
            True, is more suitable for batch processing. Defaults to False.
        sleep_time_on_not_ok (int, optional): The sleep time in seconds to wait before retrying after an HTTP error. Defaults to 10.
        num_tries_on_not_ok (int, optional): The number of tries to attempt after an HTTP error.
            If -1, then unlimited. Defaults to -1.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.
        Exception: HTTP 503 error.
        Exception: Model validation error.

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
            "max_results": str(max_results),  # Max results per response
        }

        num_tries_on_not_ok_i = num_tries_on_not_ok + 1
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

                response_text = await response.text()
                response_json = await response.json()
                if not response.ok:
                    logger.error(
                        f"Cannot get followings for user {id} with params: {params} (HTTP {response.status}): {response_text}. Response JSON: {response_json}"
                    )

                    # Raise exception on HTTP 503 if specified
                    if response.status == 503 and raise_exception_on_http_503:
                        raise Exception(response_json)

                    # Note: From experience, only HTTP 503 errors can appear here
                    # Decrement the number of tries left on HTTP error
                    if num_tries_on_not_ok_i > 0:
                        num_tries_on_not_ok_i -= 1

                    # Infinite or remaining tries on HTTP error
                    if num_tries_on_not_ok_i < 0 or num_tries_on_not_ok_i > 0:
                        await asyncio.sleep(sleep_time_on_not_ok)
                        continue

                    # num_tries_on_not_ok_i == 0, no more tries left, break the loop and return
                    else:
                        logger.error(f"Exceeded number of tries ({num_tries_on_not_ok}) on HTTP error for getting followings of user {id}.")
                        break

                try:
                    users = Get2UsersIdFollowingResponse.model_validate(response_json)
                except Exception as e:
                    if not raise_exception_on_model_validation_error:
                        logger.warning(f"Inconsistent twitter OpenAPI documentation {e}")
                        logger.warning(response_json)
                    else:
                        # Concatenate all lines of e_str into one line
                        e_str = str(e)
                        e_str = " | ".join(e_str.splitlines())
                        raise Exception(f"Inconsistent twitter OpenAPI documentation {e_str} for response: {response_json}")

                if not users.data:
                    raise Exception(users)

                for user in users.data:
                    yield user

                if "next_token" in response_json.get("meta"):
                    params["pagination_token"] = response_json.get("meta").get("next_token")
                else:
                    break
