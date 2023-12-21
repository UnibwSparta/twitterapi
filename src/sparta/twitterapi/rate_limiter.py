import asyncio
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """A utility class for handling rate limiting in API requests.

    This class provides methods to check and handle rate limits as provided
    by the API, typically through HTTP headers. It tracks the number of requests
    remaining before hitting the rate limit and the time when the rate limit
    will be reset.

    Attributes:
        remaining (Optional[int]): The number of requests left for the rate limit window.
                                   Defaults to None.
        reset_time (Optional[int]): The UTC epoch time in seconds when the rate limit
                                    will be reset. Defaults to None.

    Methods:
        wait_for_limit_reset: Asynchronously waits until the rate limit is reset if
                              the limit has been reached.
        update_limits(headers): Updates the rate limit remaining and reset time based
                                on the HTTP headers from a response.
        should_wait(): Determines whether it is necessary to wait for the rate limit
                       reset based on the remaining requests.
    """

    def __init__(self) -> None:
        self.remaining: Optional[int] = None
        self.reset_time: Optional[int] = None

    async def wait_for_limit_reset(self) -> None:
        """Asynchronously waits until the rate limit is reset.

        This method calculates the time to wait based on the current time and the
        reset time of the rate limit. It then pauses execution for that duration,
        effectively throttling the rate of API requests.

        Raises:
            Warning: If the reset time has passed but the method is called.
        """
        if self.reset_time is not None:
            wait_time = max(self.reset_time - int(time.time()), 1)  # Warte mindestens 1 Sekunde
            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds.")
            await asyncio.sleep(wait_time)

    def update_limits(self, headers: Dict[str, str]) -> None:
        """Updates the rate limit information based on the response headers.

        Args:
            headers (Dict[str, str]): A dictionary of HTTP headers from an API response.

        This method extracts the 'x-rate-limit-remaining' and 'x-rate-limit-reset'
        values from the headers and updates the internal state of the rate limiter.
        """
        self.remaining = int(headers.get("x-rate-limit-remaining", 1))
        self.reset_time = int(headers.get("x-rate-limit-reset", 0))

    def should_wait(self) -> bool:
        """Determines if waiting for rate limit reset is necessary.

        Returns:
            bool: True if the remaining number of requests is zero and it's necessary
                  to wait until the rate limit is reset. False otherwise.
        """
        return self.remaining == 0
