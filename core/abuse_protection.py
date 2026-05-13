def is_admin(user_id: str) -> bool:
    return user_id in {"YOUR_TELEGRAM_ID"}  # ← Замени на свой ID

def is_message_too_long(text: str, max_len: int = 5000) -> bool:
    return len(text) > max_len

def contains_spam(text: str) -> bool:
    spam = ["купить", "crypto", "казино", "ставки", "http", "www."]
    return any(word in text.lower() for word in spam)

def is_system_command(text: str) -> bool:
    return text.startswith(('/', '!', '.'))