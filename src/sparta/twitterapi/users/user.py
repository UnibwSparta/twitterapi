#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""user.py: Implementation of Twitter Users lookup endpoint.

"The RESTful endpoint uses the GET method to return information about a user or group of users, specified by a user ID or a username. The response
includes one or many user objects, which deliver fields such as the Follower count, location, pinned Tweet ID, and profile bio. Responses can also
optionally include expansions to return the full Tweet object for a user’s pinned Tweet, including the Tweet text, author, and other Tweet fields."
(Source: https://developer.twitter.com/en/docs/twitter-api/users/lookup/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get Users by username::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.users.user import get_users_by_username

        async for user in get_users_by_username(['projekt_sparta', 'Bundestag']):
            print(user.model_dump_json())

    Get Users by ID::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.users.user import get_users_by_ids

        async for user in get_users_by_ids(['1422600096324231168', '3088296873']):
            print(user.model_dump_json())
"""

import logging
import os
from typing import AsyncGenerator, Dict, List

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2UsersByResponse, Get2UsersResponse, User
from sparta.twitterapi.tweets.constants import USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_users_by_username(usernames: List[str]) -> AsyncGenerator[User, None]:
    """Retrieves information about users specified by their username.

    Args:
        usernames (List[str]): A List of usernames (Twitter handle). Up to 100 are allowed in a single request.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.

    Returns:
        AsyncGenerator[User, None]: AsyncGenerator that yields Twitter User objects.

    Yields:
        Iterator[AsyncGenerator[User, None]]: A Twitter User object.
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "usernames": ",".join(usernames),
            "user.fields": USER_FIELDS,
        }
        logger.debug(f"Search users params={params}")
        async with session.get("https://api.twitter.com/2/users/by", params=params) as response:
            if not response.ok:
                raise Exception(f"Cannot search users {params} (HTTP {response.status}): {await response.text()}")

            response_json = await response.text()
            try:
                users = Get2UsersByResponse.model_validate_json(response_json)
            except Exception as e:
                logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                logger.warn(response_json)
            if not users.data:
                raise Exception(users)
            for user in users.data:
                yield user


async def get_users_by_ids(ids: List[str]) -> AsyncGenerator[User, None]:
    """Retrieves information about users specified by their ID.

    Args:
        ids (List[str]): A list of User IDs. Up to 100 are allowed in a single request.

    Raises:
        Exception: Cannot get the search result due to an http error.
        Exception: User not found error.

    Returns:
        AsyncGenerator[User, None]: AsyncGenerator that yields Twitter User objects.

    Yields:
        Iterator[AsyncGenerator[User, None]]: A Twitter User object.
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "ids": ",".join(ids),
            "user.fields": USER_FIELDS,
        }
        logger.debug(f"Search users params={params}")
        async with session.get("https://api.twitter.com/2/users", params=params) as response:
            if not response.ok:
                raise Exception(f"Cannot search users {params} (HTTP {response.status}): {await response.text()}")

            response_json = await response.text()
            try:
                users = Get2UsersResponse.model_validate_json(response_json)
            except Exception as e:
                logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                logger.warn(response_json)
            if not users.data:
                raise Exception(users)
            for user in users.data:
                yield user
