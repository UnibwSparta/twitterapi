import sparta.twitterapi


# If there are no other tests this one is needed -> otherwise pytest will fail
def test_package() -> None:
    sparta.twitterapi
    assert True
