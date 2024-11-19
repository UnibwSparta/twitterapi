import pytest

from sparta.twitterapi.usage import get_usage


@pytest.mark.asyncio
async def test_get_tweets_by_id() -> None:
    usage = await get_usage()
    assert usage is not None
