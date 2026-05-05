from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

# 定义一个装饰器：最多重试 3 次，每次等待时间指数增长（1s, 2s, 4s...）
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
)
def robust_api_call(func, *args, **kwargs):
    """
    包装函数，提供自动重试功能
    """
    return func(*args, **kwargs)