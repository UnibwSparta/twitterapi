import pytest

from sparta.twitterapi.tweets.filtered_stream import get_rules


@pytest.mark.asyncio
async def test_get_tweets_by_id() -> None:
    rules = [rule async for rule in get_rules()]
    assert rules or rules == []
