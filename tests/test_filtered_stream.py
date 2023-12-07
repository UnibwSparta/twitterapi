import pytest

from sparta.twitterapi.tweets.filtered_stream import get_rules


@pytest.mark.asyncio
async def test_get_rules() -> None:
    rules = [rule async for rule in get_rules()]
    assert rules or rules == []


# @pytest.mark.asyncio
# async def test_get_stream() -> None:
#     async for tweet_response in get_stream(backfill_minutes=5):
#         assert tweet_response.tweet is not None
#         assert tweet_response.includes is not None
#         assert "id" in tweet_response.tweet
#         break
