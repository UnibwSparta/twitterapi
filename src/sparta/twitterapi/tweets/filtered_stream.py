#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""filtered_stream.py: Implementation of Twitter filtered stream endpoint.

"The filtered stream endpoint group enables developers to filter the real-time stream of public Tweets. This endpoint group’s functionality includes
multiple endpoints that enable you to create and manage rules, and apply those rules to filter a stream of real-time Tweets that will return matching public
Tweets. This endpoint group allows users to listen for specific topics and events in real-time, monitor the conversation around competitions, understand how
trends develop in real-time, and much more." (Source: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction)

Find the Open API Spec under: https://api.twitter.com/2/openapi.json

Examples:
    Get all rules::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.filtered_stream import get_rules

        rules = [rule async for rule in get_rules()]

    Add a rule::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.filtered_stream import add_or_delete_rules
        from sparta.twitterapi.models.twitter_v2_spec import AddOrDeleteRulesRequest, AddRulesRequest, RuleNoId

        rule = '(#test OR @projekt_sparta) -is:retweet'
        rule_tag = "Testrule"
        addrulesreq = AddOrDeleteRulesRequest(AddRulesRequest(add=[RuleNoId(tag=rule_tag, value=rule)]))
        print(await add_or_delete_rules(addrulesreq))

    Delete a rule::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.filtered_stream import add_or_delete_rules
        from sparta.twitterapi.models.twitter_v2_spec import AddOrDeleteRulesRequest, DeleteRulesRequest, Delete

        ruleid = '123456789'
        delrulesreq = AddOrDeleteRulesRequest(DeleteRulesRequest(delete=Delete(ids=[ruleid])))
        await add_or_delete_rules(delrulesreq)

    Delete all rules::

        import os
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.filtered_stream import get_rules, add_or_delete_rules
        from sparta.twitterapi.models.twitter_v2_spec import AddOrDeleteRulesRequest, DeleteRulesRequest, Delete

        ruleids = [rule.id async for rule in get_rules()]
        delrulesreq = AddOrDeleteRulesRequest(DeleteRulesRequest(delete=Delete(ids=ruleids)))
        await add_or_delete_rules(delrulesreq)

    Connect to stream::

        import os
        import json
        os.environ["BEARER_TOKEN"] = "xxxxxxxxxxx"
        from sparta.twitterapi.tweets.filtered_stream import get_stream

        async for tweet_response in get_stream(backfill_minutes=0):
            print(json.dumps(tweet_response.tweet))
            print(json.dumps(tweet_response.includes))
"""

import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, List

import aiohttp

from sparta.twitterapi.models.tweet_response import TweetResponse
from sparta.twitterapi.models.twitter_v2_spec import (
    AddOrDeleteRulesRequest,
    AddOrDeleteRulesResponse,
    FilteredStreamingTweetResponse,
    Rule,
    RulesLookupResponse,
)
from sparta.twitterapi.tweets.constants import EXPANSIONS, MEDIA_FIELDS, PLACE_FIELDS, POLL_FIELDS, TWEET_FIELDS, USER_FIELDS

logger = logging.getLogger(__name__)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ["BEARER_TOKEN"]
headers = {"Authorization": f"Bearer {bearer_token}", "content-type": "application/json"}


async def get_rules(ids: List[str] = None) -> AsyncGenerator[Rule, None]:
    """Returns rules from a User's active rule set.

    Args:
        ids (List[str]): A list of Rule IDs.

    Raises:
        Exception: Cannot get the rules due to an http error.

    Returns:
        AsyncGenerator[Rule, None]: AsyncGenerator that yields Twitter Rule objects.

    Yields:
        Iterator[AsyncGenerator[Rule, None]]: A Twitter Rule object.
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        params: Dict[str, str] = {
            "max_results": str(500),  # Max results per response
        }
        if ids:
            params["ids"] = ",".join(ids)

        while True:
            async with session.get("https://api.twitter.com/2/tweets/search/stream/rules", params=params) as response:
                if not response.ok:
                    raise Exception(f"Cannot get rules (HTTP {response.status}): {await response.text()}")

                lookupResponse = RulesLookupResponse.model_validate_json(await response.text())

                if not lookupResponse.data:
                    return

                for rule in lookupResponse.data:
                    yield rule

                if lookupResponse.meta.next_token:
                    params["pagination_token"] = lookupResponse.meta.next_token
                else:
                    return


async def add_or_delete_rules(rules: AddOrDeleteRulesRequest, dry_run: bool = False) -> AddOrDeleteRulesResponse:
    """Add or delete rules from a User's active rule set. Users can provide unique, optionally tagged rules to add. Users can delete their entire rule set or a
    subset specified by rule ids or values.

    Args:
        rules (AddOrDeleteRulesRequest): A Twitter AddOrDeleteRulesObject object.
        dry_run (bool, optional): Dry Run can be used with both the add and delete action, with the expected result given, but without actually taking any
            action in the system (meaning the end state will always be as it was when the request was submitted). This is particularly useful to validate rule
            changes. Defaults to False.

    Raises:
        Exception: Rules cannot be added/deleted due to an http error.

    Returns:
        AddOrDeleteRulesResponse: Returns an Twitter AddOrDeleteRulesResponse object.
    """
    params: Dict[str, str] = {"dry_run": str(dry_run)}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://api.twitter.com/2/tweets/search/stream/rules", data=rules.model_dump_json(), params=params) as response:
            if not response.ok:
                raise Exception(f"Cannot add/delete rules (HTTP {response.status}): {await response.text()}")
            return AddOrDeleteRulesResponse.model_validate_json(await response.text())


async def get_stream(
    backfill_minutes: int = 5,
    start_time: datetime = None,
    end_time: datetime = None,
) -> AsyncGenerator[TweetResponse, None]:
    """Streams Tweets matching the stream's active rule set.

    Args:
        backfill_minutes (int, optional): The number of minutes of backfill requested. Defaults to 5.
        start_time (datetime): The oldest UTC timestamp from which the Tweets will be provided. Timestamp is in second granularity and is inclusive
            (i.e. 12:00:01 includes the first second of the minute). Defaults to None.
        end_time (datetime): The newest, most recent UTC timestamp to which the Tweets will be provided. Timestamp is in second granularity and is exclusive
            (i.e. 12:00:01 excludes the first second of the minute). Defaults to None.

    Raises:
        Exception: Cannot open the stream due to an http error.

    Returns:
        AsyncGenerator[TweetResponse, None]: AsyncGenerator that yields TweetResponses.

    Yields:
        Iterator[AsyncGenerator[TweetResponse, None]]: A TweetResponse Object.
    """
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=None), read_bufsize=2**21) as session:
        params: Dict[str, str] = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
            "media.fields": MEDIA_FIELDS,
            "poll.fields": POLL_FIELDS,
            "place.fields": PLACE_FIELDS,
            "backfill_minutes": str(backfill_minutes),
        }

        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        while True:
            logger.info("Start stream")
            async with session.get("https://api.twitter.com/2/tweets/search/stream", params=params) as response:
                if not response.ok:
                    raise Exception(f"Cannot open stream (HTTP {response.status}): {await response.text()}")
                while True:
                    line = await response.content.readline()
                    if line == b"":
                        break
                    if line != b"\r\n":
                        try:
                            json_line = json.loads(line)
                            tweet = TweetResponse(tweet=json_line.get("data", {}), includes=json_line.get("includes", {}))
                            yield tweet
                            try:
                                FilteredStreamingTweetResponse.model_validate(json_line)
                            except Exception as e:
                                print(e)
                                logger.warn(f"Inconsistent twitter OpenAPI documentation {e}")
                                logger.warn(line)
                        except Exception as e:
                            logger.error(f"get_stream encountered unexpected exception: {e}")
                            logger.error(line)
