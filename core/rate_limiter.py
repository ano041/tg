from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests=15, window=60):
        self.max_requests = max_requests
        self.window = window
        self.users = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        self.users[user_id] = [t for t in self.users[user_id] if now - t < self.window]
        if len(self.users[user_id]) >= self.max_requests:
            return False
        self.users[user_id].append(now)
        return True

limiter = RateLimiter()