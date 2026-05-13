import time
from collections import defaultdict
from threading import Lock
from core.logging_config import logger

class RateLimiter:
    def __init__(self, max_requests=5, window=60.0):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, user_id):
        with self.lock:
            now = time.time()
            user_requests = [t for t in self.requests[user_id] if now - t < self.window]
            self.requests[user_id] = user_requests
            if len(user_requests) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return False
            user_requests.append(now)
            return True

limiter = RateLimiter(max_requests=5, window=60)