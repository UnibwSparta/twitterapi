# import pytest

# from sparta.twitterapi.users.follower import get_followers_by_id, get_following_by_id
# from sparta.twitterapi.users.user import get_users_by_ids, get_users_by_username


# @pytest.mark.asyncio
# async def test_get_users_by_username() -> None:
#     async for user in get_users_by_username(["projekt_sparta", "Bundestag"]):
#         assert user is not None
#         assert user.id is not None


# @pytest.mark.asyncio
# async def test_get_users_by_ids() -> None:
#     async for user in get_users_by_ids(["1422600096324231168", "3088296873"]):
#         assert user is not None
#         assert user.id is not None


# @pytest.mark.asyncio
# async def test_get_followers_by_id() -> None:
#     async for user in get_followers_by_id("1422600096324231168"):
#         assert user is not None
#         assert user.id is not None


# @pytest.mark.asyncio
# async def test_get_following_by_id() -> None:
#     async for user in get_following_by_id("1422600096324231168"):
#         assert user is not None
#         assert user.id is not None
