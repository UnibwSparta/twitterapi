import pytest

from sparta.twitterapi.compliance.compliance_stream import get_tweet_compliance_stream, get_user_compliance_stream


@pytest.mark.asyncio
async def test_get_tweet_compliance_stream() -> None:
    async for complianceEvent in get_tweet_compliance_stream(partition=1):
        assert complianceEvent
        break
    assert True


@pytest.mark.asyncio
async def test_get_user_compliance_stream() -> None:
    async for complianceEvent in get_user_compliance_stream(partition=1):
        assert complianceEvent
        break
    assert True
