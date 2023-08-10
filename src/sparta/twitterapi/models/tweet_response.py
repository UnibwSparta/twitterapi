from typing import Any, Dict

from pydantic import BaseModel


class TweetResponse(BaseModel):
    """Pydantic model to represent tweet response, as Twitter's own classes cannot be used due to inconsistencies of API and actual responses.

    Attributes
    ----------
    tweet : Dict[str, Any]
        The original tweet object.
    includes : Dict[str, Any]
        The extension objects associated with the tweet (tweets, users, media, polls, places).
    """

    tweet: Dict[str, Any]
    includes: Dict[str, Any]
