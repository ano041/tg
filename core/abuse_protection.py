import re
import os
from config import MAX_MESSAGE_LENGTH

BLOCKED_PATTERNS = [
    r"(buy\s*cheap\s*medicines?)",
    r"(cryptocurrency\s*invest)",
]
ADMIN_IDS = set(os.getenv("ADMIN_IDS", "").split(","))

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_message_too_long(text, max_length=MAX_MESSAGE_LENGTH):
    return len(text) > max_length

def contains_spam(text):
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def is_system_command(text):
    return text.startswith(("/start", "/help", "/settings"))