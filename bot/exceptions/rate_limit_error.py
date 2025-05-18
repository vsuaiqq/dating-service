class RateLimitError(Exception):
    """Ошибка при превышении лимита запросов (429)"""
    pass