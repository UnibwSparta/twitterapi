from datetime import datetime, timedelta, timezone

import pytest

from sparta.twitterapi.tweets.full_search import get_full_search, get_full_search_count
from sparta.twitterapi.tweets.quote_tweets import get_quote_tweets
from sparta.twitterapi.tweets.recent_search import get_recent_search, get_recent_search_count
from sparta.twitterapi.tweets.retweets import get_retweets
from sparta.twitterapi.tweets.tweets import get_tweets_by_id


@pytest.mark.asyncio
async def test_get_tweets_by_id() -> None:
    tweet_ids = ["1511275800758300675", "1546866845180887040"]

    async for tweet_response in get_tweets_by_id(tweet_ids):
        assert tweet_response.tweet is not None
        assert tweet_response.includes is not None
        assert "id" in tweet_response.tweet
        assert tweet_response.tweet["id"] in tweet_ids


@pytest.mark.asyncio
async def test_get_retweets_by_id() -> None:
    async for user in get_retweets("1710948847826919639"):
        assert user is not None
        assert user.id is not None


@pytest.mark.asyncio
async def test_get_full_search() -> None:
    query = "@projekt_sparta -is:retweet"
    starttime = datetime(2021, 6, 1, 0, 0)
    endtime = datetime(2021, 10, 4, 0, 0)

    async for tweet_response in get_full_search(query=query, start_time=starttime, end_time=endtime):
        assert tweet_response.tweet is not None
        assert tweet_response.includes is not None
        assert "id" in tweet_response.tweet
        break


@pytest.mark.asyncio
async def test_get_full_search_count() -> None:
    query = "@projekt_sparta -is:retweet"
    starttime = datetime(2021, 6, 1, 0, 0)
    endtime = datetime(2021, 10, 4, 0, 0)

    count = sum([count.tweet_count async for count in get_full_search_count(query=query, start_time=starttime, end_time=endtime, granularity="day")])
    assert count > 0


@pytest.mark.asyncio
async def test_get_recent_search() -> None:
    query = "#test -is:retweet"
    endtime = datetime.now(timezone.utc) - timedelta(seconds=30)
    starttime = endtime - timedelta(minutes=120)

    async for tweet_response in get_recent_search(query=query, start_time=starttime, end_time=endtime):
        assert tweet_response.tweet is not None
        assert tweet_response.includes is not None
        assert "id" in tweet_response.tweet
        break


@pytest.mark.asyncio
async def test_get_recent_search_count() -> None:
    query = "#test -is:retweet"
    endtime = datetime.now(timezone.utc) - timedelta(seconds=30)
    starttime = endtime - timedelta(minutes=120)

    count = sum([count.tweet_count async for count in get_recent_search_count(query=query, start_time=starttime, end_time=endtime, granularity="day")])
    assert count > 0


@pytest.mark.asyncio
async def test_get_quote_tweets() -> None:
    tweet_ids = ["1511275800758300675", "1594704992480690178"]

    for tweet_id in tweet_ids:
        async for tweet_response in get_quote_tweets(tweet_id):
            assert tweet_response.tweet is not None
            assert tweet_response.includes is not None
            assert "id" in tweet_response.tweet
            break
