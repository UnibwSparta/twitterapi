import pytest

from sparta.twitterapi.trends.trends import get_trends_by_woeid


@pytest.mark.asyncio
async def test_get_trends_by_woeid() -> None:
    trends = await get_trends_by_woeid(woeid=676757, max_trends=5)
    assert trends is not None
    assert len(trends) <= 5
    for trend in trends:
        assert trend
