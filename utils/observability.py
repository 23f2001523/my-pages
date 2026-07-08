import time
from collections import deque

from prometheus_client import Counter

START_TIME = time.time()

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP Requests"
)

LOGS = deque(maxlen=1000)
