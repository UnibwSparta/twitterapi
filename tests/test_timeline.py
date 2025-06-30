from datetime import datetime

import pytest

from sparta.twitterapi.users.timeline import get_user_timeline_by_id


@pytest.mark.asyncio
async def test_get_timeline() -> None:
    starttime = datetime(2021, 6, 1, 0, 0)
    endtime = datetime(2021, 10, 4, 0, 0)

    async for tweet_response in get_user_timeline_by_id(user_id="1422600096324231168", start_time=starttime, end_time=endtime):
        assert tweet_response.tweet is not None
        assert tweet_response.includes is not None
        assert "id" in tweet_response.tweet
        break
