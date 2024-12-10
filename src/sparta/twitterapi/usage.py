#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""usage.py: Implementation of Twitter Usage API endpoint.

"The Usage API in the X API v2 allows developers to programmatically retrieve their project usage. Using this endpoint, developers can keep track and
monitor the number of Posts they have pulled for a given billing cycle."
(Source: https://developer.x.com/en/docs/x-api/usage/tweets/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Retrieve usage data for your application::

        import os
        import asyncio
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.usage import get_usage

        async def main():
            usage_data = await get_usage()
            if usage_data:
                print("API Usage Information:")
                print(f"Project ID: {usage_data.project_id}")
                print(f"Daily Project Usage: {usage_data.daily_project_usage}")
                print(f"Daily Client App Usage: {usage_data.daily_client_app_usage}")
                print(f"Project Cap: {usage_data.project_cap}")
                print(f"Cap Reset Day: {usage_data.cap_reset_day}")

        asyncio.run(main())
"""
import logging
import os
from typing import Optional

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2UsageTweetsResponse, Usage

logger = logging.getLogger(__name__)

bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_usage() -> Optional[Usage]:
    """Fetches usage data from the Twitter API.

    This function retrieves detailed API usage data for the current application, including rate limits and usage counts for specific endpoints.
    The usage endpoint provides insights into how the API is being used and allows developers to monitor limits to prevent overages.

    Returns:
        Optional[Usage]: A `Usage` object containing detailed API usage information.

    Raises:
        Exception: If the request fails due to an HTTP error or other issue.

    Example:
        >>> usage_data = await get_usage()
        >>> if usage_data:
        >>>     print(usage_data.project_id, usage_data.daily_project_usage, usage_data.project_cap)
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("https://api.twitter.com/2/usage/tweets") as response:
            if not response.ok:
                logging.error(f"Cannot usage data (HTTP {response.status}): {await response.text()}")

                raise Exception
            return Get2UsageTweetsResponse.model_validate(await response.json()).data
