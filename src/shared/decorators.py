import time
from functools import wraps


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator para retry automático."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def measure_time(func):
    """Decorator para medir tempo de execução."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} levou {elapsed:.4f}s")
        return result
    return wrapper
