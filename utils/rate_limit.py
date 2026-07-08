import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse


class RateLimiter:

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.clients = defaultdict(deque)

    def check(self, client):

        now = time.time()

        bucket = self.clients[client]

        while bucket and now - bucket[0] >= self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:

            retry = max(
                1,
                int(self.window - (now - bucket[0]))
            )

            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry)
                },
                content={
                    "detail": "Rate limit exceeded"
                },
            )

        bucket.append(now)

        return None
