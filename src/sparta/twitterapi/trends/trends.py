#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""trends.py: Implementation of X Trends lookup endpoint.

The Trends lookup endpoint allows developers to get trends for a location, specified using the where-on-earth id (WOEID).
WOIEDs can be found in https://github.com/UnibwSparta/twitterapi/blob/main/src/sparta/twitterapi/trends/woeids.json

Endpoint documentation:
https://developer.x.com/en/docs/x-api/trends/introduction

Example:
    import os
    os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
    from sparta.twitterapi.trends.trends import get_trends_by_woeid


    async def main():
        woeid = 26062
        trends = await get_trends_by_woeid(woeid, max_trends=10)
        print(trends)
"""

import asyncio
import logging
import os
from typing import List

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import Get2TrendsByWoeidWoeidResponse, Trend

logger = logging.getLogger(__name__)

bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_trends_by_woeid(woeid: int, max_trends: int = 20) -> List[Trend]:
    """Asynchronously retrieves trending topics for a specified WOEID.

    Args:
        woeid (int): The where-on-earth identifier for the location.
        max_trends (int, optional): The maximum number of trends to return. Default is 20.

    Returns:
        List[Dict]: A list of trends, each containing requested fields.

    Raises:
        Exception: If an HTTP error occurs or if the request parameters are invalid.
    """
    url = f"https://api.x.com/2/trends/by/woeid/{woeid}"

    params = {"max_trends": str(max_trends)}

    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            logger.debug(f"Requesting trends for WOEID={woeid} with params={params}")
            async with session.get(url, params=params) as response:
                if response.status == 400:
                    logger.error(f"Bad request for trends (HTTP {response.status}): {await response.text()}")
                    raise Exception("Invalid request parameters.")

                if response.status == 429:
                    logger.warning("Rate limit reached, sleeping for 15 minutes.")
                    await asyncio.sleep(900)
                    continue

                if not response.ok:
                    logger.error(f"Error fetching trends (HTTP {response.status}): {await response.text()}")
                    await asyncio.sleep(10)
                    continue

                response_json = await response.json()
                trends = Get2TrendsByWoeidWoeidResponse.model_validate(response_json)
                if not trends.data:
                    raise Exception(trends)
                return trends.data
