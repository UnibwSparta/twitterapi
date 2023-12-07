#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""compliance_stream.py: Implementation of Twitter compliance stream endpoint.

"Twitter is committed to our community of developers who build with the Twitter API. As part of this commitment, we aim to make our API open and fair to
developers, safe for people on Twitter, and beneficial for the Twitter platform as a whole. It is crucial that any developer who stores Twitter content
offline, ensures the data reflects user intent and the current state of content on Twitter. For example, when someone on Twitter deletes a Tweet or their
account, protects their Tweets, edits a Tweet, or scrubs the geo information from their Tweets, it is critical for both Twitter and our developers to honor
that person’s expectations and intent." (Source: https://developer.twitter.com/en/docs/twitter-api/compliance/streams/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Start the compliance stream for tweets::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance_stream import get_tweet_compliance_stream

        async for complianceEvent in get_tweet_compliance_stream(partition=1):
            print(complianceEvent)

    Start the compliance stream for users::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.compliance.compliance_stream import get_user_compliance_stream

        async for complianceEvent in get_user_compliance_stream(partition=1):
            print(complianceEvent)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp

from sparta.twitterapi.models.twitter_v2_spec import TweetComplianceStreamResponse1, UserComplianceStreamResponse1

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_tweet_compliance_stream(
    partition: int = 1, backfill_minutes: Optional[int] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
) -> AsyncGenerator[TweetComplianceStreamResponse1, None]:
    """Get an asynchronous tweet compliance-stream as generator.

    Args:
        partition (int, optional): Must be set to 1, 2, 3 or 4. Tweet compliance events are split across 4 partitions, so 4 separate streams are needed to
            receive all events. Defaults to 1.
        backfill_minutes (Optional[int], optional): The number of minutes of backfill requested. By passing this parameter, you can recover up to five
            minutes worth of data that you might have missed during a disconnection. Defaults to None.
        start_time (Optional[datetime], optional): The earliest UTC timestamp from which the Tweet Compliance events will be provided. Defaults to None.
        end_time (Optional[datetime], optional): The latest UTC timestamp to which the Tweet Compliance events will be provided. Defaults to None.

    Raises:
        Exception: Cannot open the stream due to an http error.

    Returns:
        AsyncGenerator[TweetComplianceStreamResponse1, None]: AsyncGenerator that yields Twitter TweetComplianceStreamResponse1 objects.

    Yields:
        Iterator[AsyncGenerator[TweetComplianceStreamResponse1, None]]: A Twitter TweetComplianceStreamResponse1 object.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        params: Dict[str, Any] = {"partition": str(partition)}

        if backfill_minutes:
            params["backfill_minutes"] = backfill_minutes
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        while True:
            logger.info("Start stream")
            async with session.get("https://api.twitter.com/2/tweets/compliance/stream", params=params) as response:
                if not response.ok:
                    raise Exception(f"Cannot open compliance stream (HTTP {response.status}): {await response.text()}")
                while True:
                    line = await response.content.readline()
                    if line == b"":
                        break
                    if line != b"\r\n":
                        try:
                            json_line = json.loads(line)
                            try:
                                yield TweetComplianceStreamResponse1.model_validate_json(json_line)
                            except Exception as e:
                                logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                                logger.warn(json.dumps(json_line))
                        except Exception as e:
                            logger.error(f"get_tweet_compliance_stream encountered unexpected exception: {e}")
                            logger.error(line)


async def get_user_compliance_stream(
    partition: int = 1, backfill_minutes: Optional[int] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
) -> AsyncGenerator[UserComplianceStreamResponse1, None]:
    """Get an asynchronous user compliance-stream as generator.

    Args:
        partition (int, optional): Must be set to 1, 2, 3 or 4. User compliance events are split across 4 partitions, so 4 separate streams are needed to
            receive all events. Defaults to 1.
        backfill_minutes (Optional[int], optional): The number of minutes of backfill requested. By passing this parameter, you can recover up to five
            minutes worth of data that you might have missed during a disconnection. Defaults to None.
        start_time (Optional[datetime], optional): The earliest UTC timestamp from which the Tweet Compliance events will be provided. Defaults to None.
        end_time (Optional[datetime], optional): The latest UTC timestamp to which the Tweet Compliance events will be provided. Defaults to None.

    Raises:
        Exception: Cannot open the stream due to an http error.

    Returns:
        AsyncGenerator[UserComplianceStreamResponse1, None]: AsyncGenerator that yields Twitter UserComplianceStreamResponse1 objects.

    Yields:
        Iterator[AsyncGenerator[UserComplianceStreamResponse1, None]]: A Twitter UserComplianceStreamResponse1 object.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None)) as session:
        params: Dict[str, Any] = {"partition": str(partition)}

        if backfill_minutes:
            params["backfill_minutes"] = backfill_minutes
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        while True:
            logger.info("Start stream")
            async with session.get("https://api.twitter.com/2/users/compliance/stream", params=params) as response:
                if not response.ok:
                    raise Exception(f"Cannot open compliance stream (HTTP {response.status}): {await response.text()}")
                while True:
                    line = await response.content.readline()
                    if line == b"":
                        break
                    if line != b"\r\n":
                        try:
                            json_line = json.loads(line)
                            try:
                                yield UserComplianceStreamResponse1.model_validate_json(json_line)
                            except Exception as e:
                                logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                                logger.warn(json_line)
                        except Exception as e:
                            logger.error(f"get_user_compliance_stream encountered unexpected exception: {e}")
                            logger.error(line)
